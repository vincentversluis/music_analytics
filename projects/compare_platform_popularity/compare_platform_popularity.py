# %% HEADING
# The aim of this script is to predict when a band will release a new album. No fancy
# modelling is used, just some simple metrics and visualisation.

# %% IMPORTS
# Set paths
from pathlib import Path
import sys

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # adjust as needed
sys.path.append(str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import numpy as np
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
n_artists = 100

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

# Save to csv for later use
pd.DataFrame(artists).to_csv("../../data/artists_platform_popularity.csv", index=False)

# %% VISUALISE
# Load from csv to avoid time-consuming API calls
df = pd.read_csv("../../data/artists_platform_popularity.csv")

# Log-transform listener and follower counts
df["log_listeners"] = np.log10(df["lastfm_listener_count"] + 1)
df["log_followers"] = np.log10(df["spotify_followers"] + 1)

# Setup
genres = df["genre"].unique()

palette = plt.get_cmap("tab10").colors
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
plt.subplots_adjust(hspace=0.3, wspace=0.3)

# Top left: Popularity vs listeners
ax = axes[0, 0]
for i, genre in enumerate(genres):
    genre_df = df[df["genre"] == genre]
    ax.scatter(
        genre_df["log_listeners"],
        genre_df["spotify_popularity"],
        alpha=0.2,
        color=palette[i],
    )
    ax.scatter(
        genre_df["log_listeners"].mean(),
        genre_df["spotify_popularity"].mean(),
        s=100,
        marker="X",
        edgecolor="black",
        color=palette[i],
        label=genre,
    )
ax.set_xlabel("Last.fm listeners (log10)")
ax.set_ylabel("Spotify popularity")
ax.set_title("Spotify popularity vs Last.fm listeners")

# Top right: Popularity vs followers
ax = axes[0, 1]
for i, genre in enumerate(genres):
    genre_df = df[df["genre"] == genre]
    ax.scatter(
        genre_df["log_followers"],
        genre_df["spotify_popularity"],
        alpha=0.2,
        color=palette[i],
    )
    ax.scatter(
        genre_df["log_followers"].mean(),
        genre_df["spotify_popularity"].mean(),
        s=100,
        marker="X",
        edgecolor="black",
        color=palette[i],
    )
ax.set_xlabel("Spotify followers (log10)")
ax.set_ylabel("Spotify popularity")
ax.set_title("Spotify popularity vs Spotify followers")

# Bottom left: Followers vs listeners
ax = axes[1, 0]
for i, genre in enumerate(genres):
    genre_df = df[df["genre"] == genre]
    ax.scatter(
        genre_df["log_listeners"],
        genre_df["log_followers"],
        alpha=0.2,
        color=palette[i],
    )
    ax.scatter(
        genre_df["log_listeners"].mean(),
        genre_df["log_followers"].mean(),
        s=100,
        marker="X",
        edgecolor="black",
        color=palette[i],
    )

# Add diagonal reference line
min_val = min(df["log_listeners"].min(), df["log_followers"].min())
max_val = max(df["log_listeners"].max(), df["log_followers"].max())
ax.plot(
    [min_val, max_val], [min_val, max_val], linestyle="--", color="grey", linewidth=1
)

ax.set_xlabel("Last.fm listeners (log10)")
ax.set_ylabel("Spotify followers (log10)")
ax.set_title("Spotify followers vs Last.fm listeners")

# Bottom right: Legend
ax = axes[1, 1]
ax.axis("off")  # Hide axes
legend_handles, legend_labels = axes[0, 0].get_legend_handles_labels()
ax.legend(legend_handles, legend_labels, loc="center", title="Genres", frameon=False)

# Finish up
plt.tight_layout()
plt.show()

# %%
