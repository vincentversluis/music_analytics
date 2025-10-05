# %% HEADER

# %% IMPORTS
# Set paths
from pathlib import Path
import sys

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException
from nrclex import NRCLex
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm
import yake

from functions.lyrics import clean_lyrics, count_pronouns, get_compound_sentiment
from functions.scraping import get_artist_songs, get_genius_lyrics

# %% CONFIGS
genius_client_access_token_path = (
    "../../data/credentials/genius_client_access_token.txt"
)
with open(genius_client_access_token_path, encoding="utf-8") as f:
    genius_client_access_token = f.read()

DetectorFactory.seed = 0


# %% FUNCTIONS
def get_top_tfidf_words(
    row: np.ndarray, top_n: int = 10, include_values: bool = False
) -> list:
    """Calculates the top n words in a TF-IDF vector.

    Args:
        row (np.ndarray): A TF-IDF vector
        top_n (int, optional): Number of top words to return. Defaults to 10.
        include_values (bool, optional): If tfidf values should be included. Defaults to False.

    Returns:
        list: Top n words in the vector
    """
    row_array = row.toarray().flatten()
    top_indices = np.argsort(row_array)[-top_n:][::-1]
    if include_values:
        return [(feature_names[i], row_array[i]) for i in top_indices]
    else:
        return [feature_names[i] for i in top_indices]


# %% GET DATA
with open("../../data/Favourites.txt", encoding="utf-8") as file:
    artists = file.read().splitlines()

# Collect songs for artists
songs = []
for artist in tqdm(artists, desc="Getting Genius references to songs for artists"):
    # Reset to page 1 and run to exhausted
    page = 1
    while True:
        # Get Genius hits for page (uses cache if available)
        resp = get_artist_songs(
            artist=artist, client_access_token=genius_client_access_token, page=page
        )

        # Test if no more hits
        if not resp["response"]["hits"]:
            break

        # Collect song infos
        for song in resp["response"]["hits"]:
            # Only collect if artist is primary artist
            if not artist.lower() == song["result"]["primary_artist"]["name"].lower():
                continue
            songs.append({
                "artist": artist,
                "credited_artists": song["result"]["artist_names"],
                "title": song["result"]["title"],
                "lyrics_url": f"https://genius.com{song['result']['path']}",
            })

        page += 1

# Get lyrics (uses cache if available)
for song in tqdm(songs, desc="Getting Genius lyrics for songs"):
    url = song["lyrics_url"]
    song["lyrics"] = get_genius_lyrics(url)

##### Filter out some stuff #####

# Remove junk left over from scraping and combine into one text
for song in tqdm(songs, desc="Cleaning lyrics"):
    song["lyrics"] = clean_lyrics(song["lyrics"])

# Label language (ok, this is analysing, but I use it to remove some songs as well)
for song in tqdm(songs, desc="Detecting language"):
    # Label language
    try:
        language = detect(song["lyrics"])
    except LangDetectException:
        language = "??"
    song["language"] = language

# Remove songs with no lyrics or no English lyrics (entschuldigung, Heaven Shall Burn)
songs = [song for song in songs if song["lyrics"] and song["language"] == "en"]

# %% ANALYSE DATA

##### Analyse lyrics per song #####

for song in tqdm(songs, desc="Analysing lyrics for each song"):
    # Lyrics length
    song["lyrics_length"] = len(song["lyrics"].split())

    # Lexical diversity - ratio of unique words to total words
    song["lexical_diversity"] = len(set(song["lyrics"].split())) / len(
        song["lyrics"].split()
    )

    # Pronoun usage - add each key directly to the song datas
    pronoun_count = count_pronouns(song["lyrics"])
    # Calculate perspective - share of first person SINGULAR pronouns vs all first person pronouns
    try:
        song["perspective"] = pronoun_count["first_person_sg"] / (
            pronoun_count["first_person_sg"] + pronoun_count["first_person_pl"]
        )
    except ZeroDivisionError:
        song["perspective"] = 0
    # Calculate directness - share of second person pronouns vs all other pronouns
    try:
        song["directness"] = pronoun_count["second_person_sg_pl"] / sum(
            pronoun_count.values()
        )
    except ZeroDivisionError:
        song["directness"] = 0

    # Sentiment
    song["sentiment"] = get_compound_sentiment(song["lyrics"])

songs_df = pd.DataFrame(songs)

##### Analyse per artist #####

print("Analysing aggregated data per artist...")
# Aggregate
artist_agg_df = (
    songs_df.groupby("artist")
    .agg({
        "lyrics": " | ".join,
        "lyrics_length": "mean",
        "lexical_diversity": "mean",
        "perspective": "mean",
        "directness": "mean",
        "sentiment": "mean",
    })
    .reset_index()
)

# Top words for artist using TF-IDF
vectorizer = TfidfVectorizer(stop_words="english")  # Rely on built-in preprocessing
tfidf_matrix = vectorizer.fit_transform(artist_agg_df["lyrics"])
feature_names = vectorizer.get_feature_names_out()
artist_agg_df["top_words"] = [
    get_top_tfidf_words(tfidf_matrix[i]) for i in range(tfidf_matrix.shape[0])
]

# Keywords
kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=10)
artist_agg_df["keywords"] = artist_agg_df["lyrics"].apply(
    lambda x: {kw: score for kw, score in kw_extractor.extract_keywords(x)}
)

# Emotion
artist_agg_df["emotion_profile"] = artist_agg_df["lyrics"].apply(
    lambda x: NRCLex(x).affect_frequencies
)

# Explode keywords into one-hot-encoded columns
emotion_df = artist_agg_df["emotion_profile"].apply(pd.Series)
emotion_df = emotion_df.add_prefix("emotion_")
emotion_df = emotion_df.fillna(0)
artist_agg_df = pd.concat(
    [artist_agg_df.drop(columns=["emotion_profile"]), emotion_df], axis=1
)

# Explode emotion profile into columns with profile values
keywords_df = artist_agg_df["keywords"].apply(pd.Series)
keywords_df = keywords_df.add_prefix("keyword_")
keywords_df = keywords_df.fillna(0)
artist_agg_df = pd.concat(
    [artist_agg_df.drop(columns=["keywords"]), keywords_df], axis=1
)

# %% SAVE DATA
# Save as pickle
songs_df.to_pickle("../../data/lyrics_analysis_songs_df.pickle")
artist_agg_df.to_pickle("../../data/lyrics_analysis_artist_agg_df.pickle")

# %%
