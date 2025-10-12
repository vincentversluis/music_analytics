# %% HEADER
# Visualis the twinning of bands at festivals

# %% IMPORTS
from collections import Counter, defaultdict
from itertools import chain
import json

from matplotlib import ticker
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# %% INPUTS
artist_of_interest = "Insomnium"
top_n = 25
genre_of_interest = ""  # 'Melodic Death Metal'

# %% GET DATA
# Load data
with open("../../data/festivals.json", encoding="utf-8") as f:
    festivals = json.load(f)

# Only keep festivals with more than one artist
festivals = [festival for festival in festivals if len(festival["artists"]) > 1]

# %% ANALYSE
# Get artists and their genres
artists = chain.from_iterable([festival["artists"] for festival in festivals])
artist_genres = {artist["name"]: artist["genre"] for artist in artists}

# Get top so many performers at festivals
top_performers = Counter(
    chain.from_iterable([
        [
            artist["name"]
            for artist in festival["artists"]
            if
            # If genres of interests are defined, filter by genre
            not genre_of_interest or artist["genre"] == genre_of_interest
        ]
        for festival in festivals
    ])
)

# Collect artists that have performed at the same festival (festival twins), as long
# as one of the artists is in the genre of interest
festival_twins = defaultdict(lambda: {"festivals": [], "count": 0})
for festival in festivals:
    for artist in festival["artists"]:
        for other_artist in festival["artists"]:
            # Skip artists that have no url - they are probably very early in their career
            if not artist["url"] or not other_artist["url"]:
                continue
            # Only keep twins if at least one of the artists is in the genre of interest
            if genre_of_interest:
                if not genre_of_interest in (artist["genre"], other_artist["genre"]):
                    continue
            # Add alphabetically ordered pairs to avoid reciprocal pairs
            if artist["name"] < other_artist["name"]:
                artists = (artist["name"], other_artist["name"])
                festival_twins[artists]["festivals"].append(festival["name"])
                festival_twins[artists]["count"] += 1

# Get only artists that have performed at more than one festival and sort
top_festival_twins = {
    artists: festivals["count"]
    for artists, festivals in festival_twins.items()
    if festivals["count"] > 1
}

# %% VISUALISE
##### Top festival twins #####
# Get top 10 artists
top_10_artists = [artist for artist, _ in top_performers.most_common(10)]

# Initialize symmetric matrix
matrix = pd.DataFrame(0, index=top_10_artists, columns=top_10_artists)

# Fill in shared lineup counts
for (a, b), count in top_festival_twins.items():
    if a in top_10_artists and b in top_10_artists:
        matrix.at[a, b] = count
        matrix.at[b, a] = count

# Mask the diagonal (top left to bottom right)
mask = np.eye(len(matrix), dtype=bool)

# Plot
plt.figure(figsize=(10, 8))
sns.heatmap(
    matrix,
    mask=mask,
    annot=True,
    fmt="d",
    cmap="Blues",
    linewidths=0.5,
    linecolor="grey",
)

# Force integer ticks on colorbar
cbar = plt.gca().collections[0].colorbar
cbar.ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

# Labels and layout
plt.title("Shared lineups between top performing artists between 2022 and 2025")
plt.xticks(rotation=45, fontname="DejaVu Sans Mono")
plt.yticks(rotation=0, fontname="DejaVu Sans Mono")
plt.tight_layout()
plt.show()

# %%
##### Top performers in genre of interest #####
top_performers_sorted = top_performers.most_common(top_n)

# Extract labels and counts
labels = [artist for artist, _ in top_performers_sorted]
counts = [count for _, count in top_performers_sorted]

# Plot
plt.figure(figsize=(10, 0.25 * len(labels)))
plt.barh(labels, counts, color="#1f77b4")
plt.grid(axis="x", color="grey", linestyle="--", linewidth=0.5)
plt.xlabel("Number of appearances")
plt.title(f"Top performing {genre_of_interest.lower()} artists between 2022 and 2025")
plt.gca().invert_yaxis()
ax = plt.gca()
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

# Monospaced font for nice alignment
plt.xticks(fontname="DejaVu Sans Mono")
plt.yticks(fontname="DejaVu Sans Mono")

plt.tight_layout()
plt.show()

# %%
##### Top festival twins in genre of interest #####
top_festival_twins_sorted = sorted(
    top_festival_twins.items(), key=lambda x: x[1], reverse=True
)[:top_n]

# Format labels with centered ampersand and left/right aling
artists = chain.from_iterable([artists for artists, count in top_festival_twins_sorted])
name_chars = max([len(artist) for artist in artists])
labels = [
    f"{a:>{name_chars}} & {b:<{name_chars}}" for (a, b), _ in top_festival_twins_sorted
]
counts = [count for _, count in top_festival_twins_sorted]

# Plot
plt.figure(figsize=(10, 0.25 * len(labels)))
plt.barh(labels, counts, color="#1f77b4")
plt.grid(axis="x", color="grey", linestyle="--", linewidth=0.5)
plt.xlabel("Number of appearances")
plt.title(
    f"Top artists sharing a lineup with a {genre_of_interest.lower()} artist between 2022 and 2025"
)
plt.gca().invert_yaxis()
ax = plt.gca()
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

# Use monospaced font for nice alignment
plt.xticks(fontname="DejaVu Sans Mono")
plt.yticks(fontname="DejaVu Sans Mono")

plt.tight_layout()
plt.show()

# %%
##### Top twins with artist of interest #####
# Sort and filter
top_festival_twins_sorted = sorted(
    top_festival_twins.items(), key=lambda x: x[1], reverse=True
)
top_festival_twins_filtered = [
    (other_artist, count)
    for (a, b), count in top_festival_twins_sorted
    if artist_of_interest in {a, b}
    for other_artist in (a, b)
    if other_artist != artist_of_interest
][:top_n]

# Get max name length for alignment
name_chars = max(len(name) for name, _ in top_festival_twins_filtered)

# Format labels, right align
labels = [f"{name:>{name_chars}}" for name, _ in top_festival_twins_filtered]
counts = [count for _, count in top_festival_twins_filtered]

# Plot
plt.figure(figsize=(10, 0.25 * len(labels)))
plt.barh(labels, counts, color="#1f77b4")
plt.grid(axis="x", color="grey", linestyle="--", linewidth=0.5)
plt.xlabel("Number of Shared Festivals")
plt.title(
    f"Top artists sharing a line-up with {artist_of_interest} at between 2022 and 2025"
)
plt.gca().invert_yaxis()
ax = plt.gca()
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

# Monospaced font for nice alignment
plt.xticks(fontname="DejaVu Sans Mono")
plt.yticks(fontname="DejaVu Sans Mono")

plt.tight_layout()
plt.show()

# %%
