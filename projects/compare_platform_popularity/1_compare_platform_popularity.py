# %% HEADING
# The aim of this script is to compare the popularity of artists on music platforms

# %% IMPORTS
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
