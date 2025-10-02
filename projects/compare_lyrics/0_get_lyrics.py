# %% HEADER
# TODO: Comments
# TODO: Docstrings
# TODO: Use fetch instead of requests
# TODO: ruff
# TODO: Write something about preprocessing
# TODO: Move PRONOUNS and such to their own file

# %% IMPORTS
# Set paths
from pathlib import Path
import sys

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from functools import cache
import re

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException
from nrclex import NRCLex
import pandas as pd
from tqdm import tqdm
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import yake

from functions.scraping import get_artist_songs, get_genius_lyrics

# %% INPUTS


# %% CONFIGS
genius_client_access_token_path = "../../data/credentials/genius_client_access_token.txt"
with open(genius_client_access_token_path, encoding="utf-8") as f:
    genius_client_access_token = f.read()
    
DetectorFactory.seed = 0

# %% FUNCTIONS
@cache
def is_junk_line(line: str) -> bool:
    """Determine if a line is junk.
    
    This is a heuristic based on a sample of Genius
    lyrics. Junk lines are those that are not song lyrics, but are instead a count
    of contributors, the statement about the lyrics being lyrics or a tag such as
    [Chorus], [Verse 1], [Verse 2], etc.

    Args:
        line (str): The line to check.

    Returns:
        bool: If the line is junk.
    """    
    junk_patterns = [
        r"^\d+.*[Cc]ontributors{0,1}$",  # Contributors
        r"^.*\sLyrics$",  # (song title) Lyrics
        r"^\[.*\]$",  # [Chorus], [Verse 1], [Verse 2], ...
    ]
    junk_pattern = re.compile(r"|".join(junk_patterns))
    return bool(junk_pattern.search(line.strip()))


def get_compound_sentiment(sentence: str) -> dict:
    """Get compound sentiment for a sentence.
    
    The compound score is a number between -1.0 and +1.0. The rough meanings of the 
    scores are as follows:
    -1.0 to -0.5	Strongly Negative
    -0.5 to -0.1	Mildly Negative
    -0.1 to +0.1	Neutral
    +0.1 to +0.5	Mildly Positive
    +0.5 to +1.0	Strongly Positive
    
    Args:
        sentence (str): The sentence to get compound sentiment for.

    Returns:
        dict: The compound sentiment for the sentence.
    """
    compound_sentiment = SentimentIntensityAnalyzer().polarity_scores(sentence)['compound']
    return compound_sentiment


# Define pronouns
PRONOUNS = {
    "first_person_sg": ["i", "me", "my", "mine", "myself",],
    "first_person_pl": ["we", "us", "our", "ours", "ourselves",],
    "second_person_sg_pl": ["you", "your", "yours", "yourself", "yourselves",],
    "third_person_masc": ["he", "him", "his", "himself",],
    "third_person_fem": ["she", "her", "hers", "herself",],
    "third_person_neut": ["it", "its", "its", "itself",],
    "third_person_ep_pl": ["they", "them", "their", "theirs", "themself", "themselves",],
}

# Create regex patterns for each pronoun
PRONOUN_PATTERNS = {
    pronoun_type: re.compile(r"\b({})\b".format("|".join(PRONOUNS[pronoun_type])))
    for pronoun_type 
    in PRONOUNS
}


def count_pronouns(text: str) -> dict:
    """Count pronouns in a text.
    
    The text is converted to lower case before counting.
    
    Args:
        text (str): The text to count pronouns in.

    Returns:
        dict: The count of pronouns in the text.
    """
    pronoun_count = {
        pronoun_type: len(pattern.findall(text.lower()))
        for pronoun_type, pattern
        in PRONOUN_PATTERNS.items()
    }
    
    return pronoun_count


# %% GET DATA
with open('../../data/Favourites.txt', encoding="utf-8") as file:
    artists = file.read().splitlines()

# Collect songs for artists
songs = []
for artist in tqdm(artists, desc="Getting Genius references to songs for artists"):
    # Reset to page 1 and run to exhausted
    page = 1
    while True:
        # Get Genius hits for page (uses cache if available)
        resp = get_artist_songs(
            artist=artist, 
            client_access_token=genius_client_access_token, 
            page=page)

        # Test if no more hits
        if not resp['response']['hits']:
            break

        # Collect song infos
        for song in resp['response']['hits']:
            # Only collect if artist is primary artist
            if not artist.lower() == song['result']['primary_artist']['name'].lower():
                continue
            songs.append({
                "artist": artist,
                "credited_artists": song['result']['artist_names'],
                "title": song['result']['title'],
                "lyrics_url": f"https://genius.com{song['result']['path']}"
            })
            
        page += 1

# Get lyrics (uses cache if available)
for song in tqdm(songs, desc="Getting Genius lyrics for songs"):
    url = song['lyrics_url']
    song['lyrics'] = get_genius_lyrics(url)
    
# %% PREPARE DATA
# Remove junk left over from scraping and combine into one text
for song in tqdm(songs, desc="Cleaning lyrics"):
    song['lyrics'] = ', '.join([
        line 
        for line 
        in song['lyrics'] 
        if not is_junk_line(line) 
        and line.strip()
        ])
    
# Label language (ok, this is analysing, but I use it to remove some songs as well)
for song in tqdm(songs, desc="Detecting language"):
    # Label language
    try:
        language = detect(song['lyrics'])
    except LangDetectException:
        language = "??"
    song['language'] = language
    
# Remove songs with no lyrics or no English lyrics (entschuldigung, Heaven Shall Burn)
songs = [song for song in songs if song['lyrics'] and song['language'] == "en"]

# %% ANALYSE DATA
##### Analyse lyrics per song #####
for song in tqdm(songs, desc="Analysing lyrics for each song"):
    # Lyrics length
    song['lyrics_length'] = len(song['lyrics'].split())
    
    # Lexical diversity - ratio of unique words to total words
    song['lexical_diversity'] = len(set(song['lyrics'].split())) / len(song['lyrics'].split())
    
    # Pronoun usage - add each key directly to the song datas
    pronoun_count = count_pronouns(song['lyrics'])
    # Calculate perspective - share of first person SINGULAR pronouns vs all first person pronouns
    try:
        song['perspective'] = pronoun_count['first_person_sg'] / (pronoun_count['first_person_sg'] + pronoun_count['first_person_pl'])
    except ZeroDivisionError:
        song['perspective'] = 0
    # Calculate directness - share of second person pronouns vs all other pronouns
    try:
        song['directness'] = pronoun_count['second_person_sg_pl'] / sum(pronoun_count.values())
    except ZeroDivisionError:
        song['directness'] = 0
    
    # Sentiment
    song['sentiment'] = get_compound_sentiment(song['lyrics'])

songs_df = pd.DataFrame(songs)

# Normalise lyrics length to be a number between 0 and 1
songs_df['lyrics_length_norm'] = songs_df['lyrics_length'] / songs_df['lyrics_length'].max()

##### Analyse per artist #####
# Aggregate
artist_agg_df = (
    songs_df
    .groupby('artist')
    .agg({
        'lyrics': lambda x: ' '.join(x),
        'lyrics_length': 'mean',
        'lyrics_length_norm': 'mean',
        'lexical_diversity': 'mean',
        'perspective': 'mean',
        'directness': 'mean',
        'sentiment': 'mean'
    })
    .reset_index()
)

# Keywords
kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=10)
artist_agg_df['keywords'] = artist_agg_df['lyrics'].apply(
    lambda x: {kw: score for kw, score in kw_extractor.extract_keywords(x)}
)

# Emotion
artist_agg_df['emotion_profile'] = artist_agg_df['lyrics'].apply(lambda x: NRCLex(x).affect_frequencies)

# %%
# Explode keywords into one-hot-encoded columns
emotion_df = artist_agg_df['emotion_profile'].apply(pd.Series)
emotion_df = emotion_df.add_prefix('emotion_')
emotion_df = emotion_df.fillna(0)
artist_agg_df = pd.concat([artist_agg_df.drop(columns=['emotion_profile']), emotion_df], axis=1)

# Explode emotion profile into columns with profile values
keywords_df = artist_agg_df['keywords'].apply(pd.Series)
keywords_df = keywords_df.add_prefix('keyword_')
keywords_df = keywords_df.fillna(0)
artist_agg_df = pd.concat([artist_agg_df.drop(columns=['keywords']), keywords_df], axis=1)

# ! TODO: TF-IDF (signature vocabulary)

# %% VISUALISE DATA
# Graphs with dimensions
# Network with some generalised similarity
    
# %% PRUTS
artist_agg_df


# %%


# %%
