# %% HEADING
# The aim of this script is to collect data to investigate whether a genre is more popular

# %% IMPORTS
import pandas as pd
from tqdm import tqdm

from functions.scraping import (
    get_genre_artists,
    get_lastfm_listener_count,
    get_spotify_artist,
)

# %% INPUTS
genres = [
    "melodic death metal",
    "atmospheric black metal",
    "thrash metal",
    "hardcore punk",
    "punk rock",
    "ska punk",
    "crossover jazz",
    "east coast hip hop",
    "indie rock",
]
n_artists = 3

# %% CONFIGS
lastfm_api_key_path = "../../data/credentials/lastfm_credentials.txt"
spotify_client_id_path = "../../data/credentials/spotify_client_id.txt"
spotify_client_secret_path = "../../data/credentials/spotify_client_secret.txt"

# Get keys and such
with open(lastfm_api_key_path, encoding="utf-8") as f:
    lastfm_api_key = f.read()
with open(spotify_client_id_path, encoding="utf-8") as f:
    spotify_client_id = f.read()
with open(spotify_client_secret_path, encoding="utf-8") as f:
    spotify_client_secret = f.read()

# %% GET DATA
# Get some artists in each genre and collect data
artists = []
for genre in genres:
    genre_artists = get_genre_artists(genre, n_artists)
    for artist in tqdm(genre_artists, desc=f"Getting artists for {genre}"):
        lastfm_listener_count = get_lastfm_listener_count(
            artist["name"], lastfm_api_key
        )
        spotify_data = get_spotify_artist(
            artist["name"], spotify_client_id, spotify_client_secret
        )
        # Not every artist has a Spotify data
        spotify_followers = spotify_data["followers"]["total"] if spotify_data else None
        spotify_popularity = spotify_data["popularity"] if spotify_data else None

        artists.append({
            "name": artist["name"],
            "genre": genre,
            "lastfm_listener_count": lastfm_listener_count,
            "spotify_followers": spotify_followers,
            "spotify_popularity": spotify_popularity,
        })

# %% SAVE DATA
# Save to csv for later use
pd.DataFrame(artists).to_csv("../../data/artists_platform_popularity.csv", index=False)

# %%
