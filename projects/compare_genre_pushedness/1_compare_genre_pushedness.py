"""The aim of this script is to make a visualisation of genre pushedness on Spotify."""

# %% IMPORTS
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# %% INPUTS
remove_outliers = 0.05  # Remove outliers in the top and bottom pct of this proportion
listeners_min = 10_000  # Minimum monthly listeners to keep an artist

# %% GET DATA
# Load from pickle to avoid time-consuming API calls
df = pd.read_pickle("../../data/genre_artists_followers_listeners.pkl")

# Not every artist has numbers available (for any reason), remove those
df = df.dropna().copy()

# Only keep artists with at least 10_000 monthly listeners
df = df[df["listeners_spotify"] > listeners_min]

# Calculate pushedness
df["pushedness"] = df["listeners_spotify"] / df["followers_spotify"]

# Remove outliers in pushedness - remove the top and bottom so many percent
df = df[
    df["pushedness"].between(
        df["pushedness"].quantile(remove_outliers),
        df["pushedness"].quantile(1 - remove_outliers),
    )
]

# Recalculate df_genre with medians
df_genre = df.groupby("genre", as_index=False).agg(
    median_followers=("followers_spotify", "median"),
    median_listeners=("listeners_spotify", "median"),
    median_pushedness=("pushedness", "median"),
)

# Sort genres by median pushedness
df_genre_sorted = df_genre.sort_values("median_pushedness", ascending=False)

# %% VISUALISE
fig, ax = plt.subplots(figsize=(10, 10))
spacing = 1.5

# Add artist by artist
for idx, row in enumerate(df_genre_sorted.itertuples()):
    # Get values to plot
    genre = row.genre
    median_val = row.median_pushedness
    genre_rows = df.loc[df["genre"] == genre]
    genre_vals = genre_rows["pushedness"]
    y = idx * spacing

    # All artists
    plt.scatter(genre_vals, [y] * len(genre_vals), color="black", alpha=0.3, s=20)

    # Median point and label
    plt.scatter(median_val, y, color="black", s=50, zorder=3)
    plt.text(
        median_val,
        y + 0.5,
        f"{median_val:.2f}",
        va="bottom",
        ha="center",
        fontsize=9,
        color="black",
    )

    # Top listened artist (italic label)
    top_band_row = genre_rows.loc[genre_rows["listeners_spotify"].idxmax()]
    plt.annotate(
        top_band_row["artist"],
        xy=(top_band_row["pushedness"], y),
        xytext=(top_band_row["pushedness"], y - 0.4),
        ha="center",
        va="bottom",
        fontsize=8,
        color="black",
        fontstyle="italic",
        arrowprops=dict(arrowstyle="-", color="black", lw=0.6, shrinkA=0, shrinkB=0),
    )

    # Highest pushed (dark green)
    top_pushed_row = genre_rows.loc[genre_rows["pushedness"].idxmax()]
    plt.scatter(top_pushed_row["pushedness"], y, color="darkgreen", s=40, zorder=3)
    plt.annotate(
        top_pushed_row["artist"],
        xy=(top_pushed_row["pushedness"], y),
        xytext=(top_pushed_row["pushedness"], y + 0.4),
        ha="center",
        va="bottom",
        fontsize=8,
        color="darkgreen",
        arrowprops=dict(
            arrowstyle="-", color="darkgreen", lw=0.6, shrinkA=0, shrinkB=0
        ),
    )

    # Lowest pushed (dark red)
    bottom_pushed_row = genre_rows.loc[genre_rows["pushedness"].idxmin()]
    plt.scatter(bottom_pushed_row["pushedness"], y, color="darkred", s=40, zorder=3)
    plt.annotate(
        bottom_pushed_row["artist"],
        xy=(bottom_pushed_row["pushedness"], y),
        xytext=(bottom_pushed_row["pushedness"], y - 0.4),
        ha="center",
        va="top",
        fontsize=8,
        color="darkred",
        arrowprops=dict(arrowstyle="-", color="darkred", lw=0.6, shrinkA=0, shrinkB=0),
    )

# Vertical reference lines
max_val = int(np.ceil(df["pushedness"].max()))
for x in range(1, max_val + 1):
    plt.axvline(x, color="lightgray", linestyle="--", linewidth=0.7, alpha=0.7)

# Legend handles
legend_handles = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="darkred",
        markersize=8,
        label="Lowest pushed artist in genre",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="darkgreen",
        markersize=8,
        label="Highest pushed artist in genre",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="black",
        markersize=8,
        label="Median pushedness of genre",
    ),
    mpatches.Patch(
        facecolor="none", edgecolor="none", label="Top listened artist in genre"
    ),
]

# Legend below plot
legend = plt.legend(
    handles=legend_handles,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.05),
    ncol=2,
    fontsize=9,
    frameon=True,
)

# Stylise legend texts
for text in legend.get_texts():
    t = text.get_text()
    if t == "Lowest pushed artist in genre":
        text.set_color("darkred")
    elif t == "Highest pushed artist in genre":
        text.set_color("darkgreen")
    elif t == "Median pushedness of genre":
        text.set_color("black")
    elif t == "Top listened artist in genre":
        text.set_color("black")
        text.set_fontstyle("italic")


# Axes and more layout
plt.yticks([i * spacing for i in range(len(df_genre_sorted))], df_genre_sorted["genre"])
plt.xlabel("Spotify pushedness (monthly listeners / followers)")
plt.ylabel("Genre")
ax.set_title(
    "Spotify artist pushedness per genre",
    fontsize=14,
    fontweight="bold",
    loc="center",
    pad=20,
)
ax.text(
    0.5,
    1.01,
    "The ratio of monthly Spotify listeners / followers of the leading artists in each genre as found on Last.fm",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=10,
    style="italic",
    color="#555555",
)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

# %%
