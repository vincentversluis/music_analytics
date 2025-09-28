# %% HEADER
# TODO: Comments
# TODO: Docstrings
# TODO: Use fetch instead of requests
# TODO: ruff

# %% IMPORTS
# Set paths
from pathlib import Path
import sys

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import re

import pandas as pd
from tqdm import tqdm

from functions.scraping import get_artist_songs, get_genius_lyrics

# %% INPUTS
...

# %% CONFIGS
genius_client_access_token_path = "../../data/credentials/genius_client_access_token.txt"
with open(genius_client_access_token_path, encoding="utf-8") as f:
    genius_client_access_token = f.read()
    
# %% GET DATA
bands_path = "../../data/bands.csv"
artists_df = pd.read_csv(bands_path, delimiter=";")
artists = artists_df["Band"].to_list()[:25]  # Just the first so many

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
            # Only collect if artist is in credited artists
            if not re.search(
                rf'\b{artist}\b', 
                song['result']['artist_names'], re.IGNORECASE):
                continue
            songs.append({
                "artist": artist,
                "credited_artists": song['result']['artist_names'],
                "title": song['result']['title'],
                "lyrics_url": f"https://genius.com{song['result']['path']}"
            })
            
        page += 1

print(f"Found {len(songs)} songs")

# %%
# Get lyrics (uses cache if available)
for song in tqdm(songs, desc="Getting lyrics"):
    url = song['lyrics_url']
    song['lyrics'] = get_genius_lyrics(url)
    
# %% PREPARE DATA
# Remove some junk from lyrics
