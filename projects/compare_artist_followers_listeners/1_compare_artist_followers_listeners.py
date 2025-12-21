"""The aim of this script is to make a visualisation of followers of artists performing at 70K tons of metal.

Also show the amount of listeners, to make this a two dimensionalplot and add some context.
"""

# %% IMPORTS
from adjustText import adjust_text
from matplotlib import ticker
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# %% INPUTS
year = 2025

# %% GET DATA
# Load from csv to avoid time-consuming API calls
df = pd.read_csv(f"../../data/artists_70K_{year}_abt.csv", sep=";")

# %% VISUALISE
# Safety for log scales (at least 1 listener and follower)
df = df[
    (df["listeners_spotify"] >= 1) &
    (df["followers_spotify"] >= 1)
]

sns.set(style="whitegrid")
plt.figure(figsize=(12, 12))

# Add podium colour if column exists
if "podium_largest" in df.columns:
    ax = sns.scatterplot(
        data=df,
        x="listeners_spotify",
        y="followers_spotify",
        hue="podium_largest",
        palette="tab10",
        s=30,
        linewidth=0
    )
else:
    ax = sns.scatterplot(
        data=df,
        x="listeners_spotify",
        y="followers_spotify",
        color="black",
        s=30,
        linewidth=0
    )

# Axes
ax.set_xscale("log")
ax.set_yscale("log")
ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=10))
ax.yaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=10))
ax.xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, _: f"{int(x):,}")
)
ax.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda y, _: f"{int(y):,}")
)
ax.grid(True, which="both", linestyle=":", linewidth=0.5)

# Labels and possible clipping
texts = []
for _, row in df.iterrows():
    x_jitter = row["listeners_spotify"] * 1.01
    y_jitter = row["followers_spotify"] * 1.01
    t = ax.text(
        x_jitter,
        y_jitter,
        row["artist"],
        fontsize=10,
        color="black",
        alpha=0.8,
    )
    t.set_clip_on(True)
    texts.append(t)

# Adjust labels with constraints
adjust_text(
    texts,
    ax=ax,
    expand_points=(1.1, 1.1),
    expand_text=(1.2, 1.2),
    force_text=0.6,
    force_points=0.4,
    only_move={"points": "y", "text": "y"},
    arrowprops=dict(arrowstyle="-", color="gray", lw=0.5),
    lim=300,
    precision=0.02,
)

# Titles and labels
plt.title(f"Spotify listeners vs followers of artists performing at 70000 tons of metal {year}")
plt.xlabel("Listeners (log scale)")
plt.ylabel("Followers (log scale)")

xmin, xmax = ax.get_xlim()
ymin, ymax = ax.get_ylim()

ax.set_xlim(left=100, right=xmax)
ax.set_ylim(bottom=100, top=ymax)

# Add legend for podium if column exists
if "podium_largest" in df.columns:
    ax.legend(title="Largest podium", bbox_to_anchor=(1.02, 1), loc="upper left")

plt.tight_layout()
plt.show()

# %%
