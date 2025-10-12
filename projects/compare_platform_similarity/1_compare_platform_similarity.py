# %% HEADING
# The aim of this script is to predict when a band will release a new album. No fancy
# modelling is used, just some simple metrics and visualisation.

# %% IMPORTS
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

from functions.scraping import get_lastfm_listener_count, get_similar_artists

# %% INPUTS
artists = ["Aephanemer", "Dark Tranquillity", "Metallica"]
similar_artists_n = 666  # Number of similar artists to get on Last.fm

top_similar_n = 3  # Number of most similar artists to label on plot
top_discrapancy_n = 5  # Number of most discrepant artists to label on plot

# %% CONFIGS
lastfm_api_key_path = "../../data/credentials/lastfm_credentials.txt"
with open(lastfm_api_key_path, encoding="utf-8") as f:
    lastfm_api_key = f.read()

# %% GET DATA
# Get saved Encyclopaedia Metallum data
df_metallum_all = pd.read_csv("../../data/artists_platform_similarity_metallum.csv")

lastfm_data = {}
for artist in tqdm(artists, desc="Getting Last.fm data"):
    lastfm_data[artist] = {}
    # Similar artists and similarity score
    lastfm_data[artist]["similar_artists"] = pd.DataFrame(
        get_similar_artists(
            artist_name=artist, lastfm_api_key=lastfm_api_key, limit=similar_artists_n
        )
    )
    # Listener count
    lastfm_data[artist]["listener_count"] = get_lastfm_listener_count(
        artist_name=artist, lastfm_api_key=lastfm_api_key
    )

# %% PREPARE DATA
# Create dataframes for each artist
data = {}
for artist in artists:
    # Get data in happy format
    df_lastfm = lastfm_data[artist]["similar_artists"][["name", "similarity"]].copy()
    df_lastfm.rename(
        columns={"name": "similar_artist", "similarity": "score_lastfm"}, inplace=True
    )

    df_metallum = df_metallum_all[df_metallum_all["artist"] == artist][
        ["similar_artist", "score"]
    ]
    df_metallum.rename(columns={"score": "score_metallum"}, inplace=True)

    # Combine dataframes on artist name
    df = pd.merge(df_metallum, df_lastfm, on="similar_artist", how="left")

    # Remove similar artists that do not appear in both sets
    df.dropna(inplace=True)

    # Add ranks
    df["rank_metallum"] = df["score_metallum"].rank(method="min", ascending=False)
    df["rank_lastfm"] = df["score_lastfm"].rank(method="min", ascending=False)

    # Calculate correlation (Spearman for ranked data)
    correlation = df["rank_metallum"].corr(df["rank_lastfm"], method="spearman")

    data[artist] = {
        "correlation": correlation,
        "similarities": df,
        "listener_count": lastfm_data[artist]["listener_count"],
    }

# %% VISUALISE
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for ax, (artist, artist_data) in zip(axes, data.items(), strict=False):
    df = artist_data["similarities"].copy()
    corr = artist_data["correlation"]
    listener_count = artist_data["listener_count"]
    x, y = df["rank_lastfm"], df["rank_metallum"]

    ax.scatter(x, y, alpha=0.5, label="Other artists", color="royalblue")

    # Diagonal line
    min_rank = min(x.min(), y.min())
    max_rank = max(x.max(), y.max())
    ax.plot([min_rank, max_rank], [min_rank, max_rank], linestyle="--", color="dimgrey")

    # Title with correlation
    ax.set_title(f"{artist} ({listener_count:,} Last.fm listeners)\nR={corr:.2f}")

    # Axis labels and ticks
    tick_step = max(1, int((max_rank - min_rank) // 5))
    ax.set_xlabel("Last.fm rank")
    ax.set_ylabel("Encyclopaedia Metallum rank")
    ax.set_xticks(range(int(min_rank), int(max_rank) + 1, tick_step))
    ax.set_yticks(range(int(min_rank), int(max_rank) + 1, tick_step))
    ax.grid(True, linestyle="--", alpha=0.5)

    # Label interesting points - keep track of what has been labeled
    labeled = set()

    # Top n similar artists
    # top_similar = df.nsmallest(top_similar_n, ['rank_lastfm', 'rank_metallum'])
    df["total_similarity"] = df["rank_lastfm"] + df["rank_metallum"]
    top_similarities = df.nsmallest(top_similar_n, "total_similarity")
    # top_similarities = df.sort_values('total_similarity', ascending=False)
    count = 0
    for _, row in top_similarities.iterrows():
        name = row["similar_artist"]
        if name not in labeled:
            ax.scatter(
                row["rank_lastfm"], row["rank_metallum"], color="black", s=50, zorder=3
            )
            ax.annotate(
                name,
                (row["rank_lastfm"], row["rank_metallum"]),
                textcoords="offset points",
                xytext=(5, -10),
                ha="left",
                fontsize=9,
                color="black",
            )
            labeled.add(name)

    # Top n discrepancies
    df["discrepancy"] = (df["rank_lastfm"] - df["rank_metallum"]).abs()
    top_discrepancies = df.sort_values("discrepancy", ascending=False)
    count = 0
    for _, row in top_discrepancies.iterrows():
        name = row["similar_artist"]
        if name not in labeled:
            ax.scatter(
                row["rank_lastfm"],
                row["rank_metallum"],
                color="dimgrey",
                s=50,
                zorder=3,
            )
            ax.annotate(
                name,
                (row["rank_lastfm"], row["rank_metallum"]),
                textcoords="offset points",
                xytext=(5, 5),
                ha="left",
                fontsize=9,
                color="dimgrey",
            )
            labeled.add(name)
            count += 1
            if count == top_discrapancy_n:
                break

    # Legend
    legend_elements = [
        Line2D(
            [0], [0], marker="o", color="black", label="Top similarity", markersize=8
        ),
        Line2D(
            [0], [0], marker="o", color="dimgrey", label="Top discrepancy", markersize=8
        ),
        Line2D(
            [0], [0], marker="o", color="royalblue", label="Other artists", markersize=8
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

plt.tight_layout()
plt.show()

# %%
