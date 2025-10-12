# %% HEADER
# Visualise some properties of artists' lyrics

# %% IMPORTS
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import pandas as pd

# %% CONFIGS
top_n = 5  # Number of artists to show on top
bottom_n = 5  # Number of artists to show on bottom
min_song_count = 10  # Minimum number of songs an artist must have to be included
lyrics_len_outlier_threshold = (
    0.99  # Threshold for removing suspiciously lengthy lyrics
)

# Load data
songs_df = pd.read_pickle("../../data/lyrics_analysis_songs_df.pickle")
artist_agg_df = pd.read_pickle("../../data/lyrics_analysis_artist_agg_df.pickle")

# Keep interesting columns to visualise
songs_df = songs_df[["artist", "lyrics_length", "lexical_diversity", "sentiment"]]
artist_agg_df = artist_agg_df[
    [
        "artist",
        "perspective",
        "directness",  # Aggregation seems to say more than details
        "emotion_anger",
        "emotion_sadness",
        "emotion_joy",
    ]
]


# %% Nice detail visualisation
song_columns = ["lyrics_length", "lexical_diversity", "sentiment"]
fig, axes = plt.subplots(1, len(song_columns), figsize=(15, 6), sharey=False)

# Prefilter lyrics_length outliers
lyrics_threshold = songs_df["lyrics_length"].quantile(lyrics_len_outlier_threshold)
filtered_df = songs_df[songs_df["lyrics_length"] <= lyrics_threshold].copy()

# Filter artists with at least so many songs
artist_counts = filtered_df["artist"].value_counts()
valid_artists = artist_counts[artist_counts >= min_song_count].index
filtered_df = filtered_df[filtered_df["artist"].isin(valid_artists)]

for i, col in enumerate(song_columns):
    ax = axes[i]

    # Compute artist level means for ranking
    artist_means = filtered_df.groupby("artist")[col].mean().sort_values()
    top_artists = artist_means.head(top_n).index.tolist()
    bottom_artists = artist_means.tail(bottom_n).index.tolist()
    selected_artists = top_artists + bottom_artists

    # Subset data
    subset_df = filtered_df[filtered_df["artist"].isin(selected_artists)]

    # Assign vertical positions with spacer
    spacer_offset = 0.4
    artist_positions = {}
    for j, artist in enumerate(top_artists):
        artist_positions[artist] = j
    for j, artist in enumerate(bottom_artists):
        artist_positions[artist] = j + len(top_artists) + spacer_offset

    # Plot density points
    for artist in selected_artists:
        artist_data = subset_df[subset_df["artist"] == artist]
        y = [artist_positions[artist]] * len(artist_data)
        ax.scatter(artist_data[col], y, color="grey", alpha=0.2, s=20, zorder=2)

    # Plot artist level means
    for artist in selected_artists:
        mean_val = artist_means[artist]
        y = artist_positions[artist]
        ax.scatter(mean_val, y, color="black", s=60, zorder=3)

    # Axis styling
    # Title
    match col:
        case "lyrics_length":
            ax.set_title("Lyrics length (total words)")
        case "lexical_diversity":
            ax.set_title("Fraction of unique words")
        case "sentiment":
            ax.set_title("Sentiment (negative (-1.0) to positive (+1.0))")

    if col == "sentiment":
        ax.set_xlim(left=-1)
    else:
        ax.set_xlim(left=0)
    ax.set_yticks([])
    ax.set_yticklabels([])
    for artist, y in artist_positions.items():
        ax.text(x=ax.get_xlim()[0], y=y, s=artist, va="center", ha="right", fontsize=9)
    ax.invert_yaxis()

# Finish up
fig.text(
    0.5,
    1.05,
    "Song-level distributions per artist: Lyrical complexity and sentiment",
    ha="center",
    va="top",
    fontsize=14,
    weight="bold",
)

# Define custom legend handles
legend_elements = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="grey",
        alpha=0.2,
        linestyle="None",
        markersize=8,
        label="Unique song metric",
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="black",
        linestyle="None",
        markersize=8,
        label="Artist mean",
    ),
]

fig.legend(
    handles=legend_elements,
    loc="lower center",
    ncol=2,
    frameon=False,
    bbox_to_anchor=(0.5, -0.05),  # x=0.5 centers it, y=-0.05 pushes it lower
)

fig.subplots_adjust(bottom=0.25)  # increase to make room for the legend

plt.tight_layout()
plt.show()

# %% Nice aggregation
emotion_columns = [
    "perspective",
    "directness",
    "emotion_joy",
    "emotion_anger",
    "emotion_sadness",
]
fig, axes = plt.subplots(1, len(emotion_columns), figsize=(15, 6), sharey=False)

for i, col in enumerate(emotion_columns):
    ax = axes[i]

    # Filter out values outside of 0-1 range, these signify very little and confouning data
    filtered = artist_agg_df[(artist_agg_df[col] > 0) & (artist_agg_df[col] < 1)].copy()

    # Sort by column
    sorted_df = filtered.sort_values(col)
    top_artists = sorted_df.head(top_n)
    bottom_artists = sorted_df.tail(bottom_n)
    selected_df = pd.concat([top_artists, bottom_artists])

    # Assign vertical positions with spacer
    spacer_offset = 0.4
    artist_positions = {}
    for j, artist in enumerate(top_artists["artist"]):
        artist_positions[artist] = j
    for j, artist in enumerate(bottom_artists["artist"]):
        artist_positions[artist] = j + len(top_artists) + spacer_offset

    # Compute maximum value for guide lines
    col_max = selected_df[col].max()

    # Split guide lines
    for _, row in selected_df.iterrows():
        artist = row["artist"]
        y = artist_positions[artist]
        x_val = row[col]
        ax.plot([0, x_val], [y, y], color="black", linewidth=1.2, zorder=1)

    # Data points
    for _, row in selected_df.iterrows():
        artist = row["artist"]
        y = artist_positions[artist]
        ax.scatter(row[col], y, color="black", edgecolor="white", s=80, zorder=2)

    # Axis styling
    match col:
        case "perspective":
            ax.set_title("Perspective (use of $\it{we}$ (0.0) vs $\it{you}$ (1.0))")
        case "directness":
            ax.set_title("Directedness (use of $\it{you}$)")
        case "emotion_joy":
            ax.set_title("Joy")
        case "emotion_anger":
            ax.set_title("Anger")
        case "emotion_sadness":
            ax.set_title("Sadness")

    # ax.set_title(col.replace('emotion_', '').capitalize())
    ax.set_xlim(left=0, right=col_max * 1.05)
    ax.set_yticks([])
    ax.set_yticklabels([])
    for artist, y in artist_positions.items():
        ax.text(x=0, y=y, s=artist, va="center", ha="right", fontsize=9)
    ax.invert_yaxis()

fig.text(
    0.5,
    1.05,
    "Artist-level profiles: Lyrical use of pronouns and emotional expression",
    ha="center",
    va="top",
    fontsize=14,
    weight="bold",
)
plt.tight_layout()
plt.show()

# %%
