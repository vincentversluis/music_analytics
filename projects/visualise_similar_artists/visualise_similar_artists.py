# %% HEADER
# Create some visualisations of similar artists.
#
# How to use:
# 0) This is an interactive script with the VS Code Jupyter code cells extension, so run this cell by cell
# 1) Get API key for Last.fm (https://www.last.fm/api/account/create)and dump this into a .txt file in ../data/credentials/lastfm_credentials.txt
# 2) Choose inputs in the input section below
# 3) Run the script cell by cell
# 4) ???
# 5) Profit
#
# Depending on the number of artists, labels might get crammed and overlap, so you
# might want to adjust the size of the plot and the number of artists to visualise
# manually.

# %% INPUTS
artist_name = "Aephanemer"
artists_n = 10  # Number of similar artists to get

# %% SET PATHS
import os
import sys

module_path = os.path.abspath(os.path.join("../../", "functions"))
if module_path not in sys.path:
    sys.path.append(module_path)

# %% IMPORTS
# import requests
from time import sleep

from adjustText import adjust_text
from matplotlib import ticker
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scraping import get_lastfm_listener_count, get_similar_artists
import seaborn as sns
from tqdm import tqdm

# %% CONFIGS
back_off = 1.5  # Seconds to wait between requests
lastfm_api_key_path = "../../data/credentials/lastfm_credentials.txt"

with open(lastfm_api_key_path, encoding="utf-8") as f:
    lastfm_api_key = f.read()

# %% GET DATA
# Get similar artists
similar_artists = get_similar_artists(
    artist_name=artist_name, limit=artists_n, lastfm_api_key=lastfm_api_key
)
sleep(back_off)  # Don't hammer the server

# Get artist's listener count as a reference
artist_listener_count = get_lastfm_listener_count(
    artist_name=artist_name, lastfm_api_key=lastfm_api_key
)

# Get listener count for each similar artist
for artist in tqdm(
    similar_artists, desc=f"Getting listener counts at 1 request per {back_off} seconds"
):
    artist["listener_count"] = int(
        get_lastfm_listener_count(artist["name"], lastfm_api_key=lastfm_api_key)
    )
    sleep(back_off)  # Don't hammer the server
df = pd.DataFrame(similar_artists)

# %% PREPARE DATA
_df = df[df["listener_count"] > artist_listener_count * 0.9]

# %% VISUALISE
# Set up the plot
sns.set(style="whitegrid")
plt.figure(figsize=(12, 12))
ax = sns.scatterplot(data=_df, x="listener_count", y="similarity", color="black")
ax.set_xscale("log")

# Add artist names as labels
texts = [
    ax.text(
        row["listener_count"],
        row["similarity"],
        row["name"],
        fontsize=13,
        color="black",
    )
    for _, row in _df.iterrows()
]
adjust_text(texts, arrowprops=dict(arrowstyle="-", color="gray"))

# Add reference line for artist
ax.axvline(
    x=artist_listener_count,
    color="black",
    linestyle="--",
    linewidth=1.5,
    label=f"{artist_name} listener count ({artist_listener_count:,})",
)

# Format axes
ax.xaxis.set_minor_locator(
    ticker.LogLocator(base=10.0, subs=np.arange(1.0, 10.0), numticks=100)
)
ax.grid(True, which="minor", linestyle=":", linewidth=0.5, color="gray")
ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, subs=[1.0, 5.0], numticks=10))
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f"))

# Customize labels and limits
plt.title("Similarity vs listener count (source: last.fm)")
plt.xlabel("Listener count (log)")
plt.ylabel(f"Relative similarity to {artist_name}")
plt.ylim(0, 1.05)  # Slightly above 1 to make room for labels

# Wrap up
ax.legend()
plt.tight_layout()
plt.show()

# %%
