"""The aim of this script is to collect data to investigate genre pushedness on Spotify."""

# %% IMPORTS
from time import sleep

from mullpy import switch_mullvad_random_server
import pandas as pd
from tqdm import tqdm

from functions.scraping import (
    get_lastfm_genre_artists,
    get_spotify_followers_and_listeners,
)

# %% INPUTS
genres = [
    "melodic death metal",
    "blackened death metal",
    "technical death metal",
    "atmospheric black metal",
    "symphonic metal",
    "thrash metal",
    "gothic metal",
    "doom metal",
    "industrial metal",
    "death metal",
    "glam metal",
    "metalcore",
    "power metal",
    "groove metal",
    "deathcore",
]
n_artists_collect = 100  # How many artists to collect in each genre
n_top_artists_analyse = 35  # Top artists to analyse in detail

scrapes_before_vpn_switch = 10  # How many scrapes before switching VPN endpoint

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
genre_artists = []
for genre in tqdm(genres, desc="Getting artists for genres"):
    artists = get_lastfm_genre_artists(genre, lastfm_api_key, n_artists_collect)
    print(f"Found {len(artists)} artists for {genre}")

    for artist in artists:
        if artists[artist]["rank"] <= n_top_artists_analyse:
            genre_artists.append({
                "artist": artist,
                "genre": genre,
                "genre_rank": artists[artist]["rank"],
            })

# Collect all artists for analysis as a set, as some artists may appear multiple times
artists = list(set([artist["artist"] for artist in genre_artists]))
print(f"\nFound {len(artists)} different artists across {len(genres)} genres")

# Get Spotify followers and listeners for an artist
vpn_countdown = scrapes_before_vpn_switch  # Countdown to switch VPN endpoints
for artist in tqdm(genre_artists, desc="Getting Spotify followers and listeners"):
    # print(artist)
    # Not all artists have a Spotify page, resulting in None followers and listeners
    if followers_and_listeners := get_spotify_followers_and_listeners(
        artist["artist"], spotify_client_id, spotify_client_secret
    ):
        artist.update(followers_and_listeners)

    # Switch VPN every so many requests
    vpn_countdown -= 1
    if vpn_countdown == 0:
        switch_mullvad_random_server()
        sleep(5)  # Wait for relay to properly switch
        vpn_countdown = scrapes_before_vpn_switch  # Reset countdown

# %% SAVE DATA
# Create a pickle file for later use
pd.DataFrame(genre_artists).to_pickle(
    "../../data/genre_artists_followers_listeners.pkl"
)

# %%
