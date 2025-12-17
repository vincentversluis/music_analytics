"""The aim of this script is to make a visualisation of followers of artists performing at 70K tons of metal.

Also show the amount of listeners, to make this a two dimensionalplot and add some context.
"""

# %% IMPORTS
from adjustText import adjust_text
from matplotlib import ticker
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# %% GET DATA
# Load from csv to avoid time-consuming API calls
df = pd.read_csv("../../data/artists_70K_2025_followers_listeners.csv", sep=";")

# %% VISUALISE
# Guarantee safety for log scales
df = df[
    (df["listeners_spotify"] > 0) &
    (df["followers_spotify"] > 0)
]

sns.set(style="whitegrid")
plt.figure(figsize=(12, 12))

ax = sns.scatterplot(
    data=df,
    x="listeners_spotify",
    y="followers_spotify",
    color="black",
    s=20,
    linewidth=0
)

# Set log scales
ax.set_xscale("log")
ax.set_yscale("log")

# Axes
ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=10))
ax.yaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=10))

ax.xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, _: f"{int(x):,}")
)
ax.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda y, _: f"{int(y):,}")
)

ax.grid(True, which="both", linestyle=":", linewidth=0.5)

# Add label at initial placement, then adjust with constraints
texts = []
for _, row in df.iterrows():
    t = ax.text(
        row["listeners_spotify"],
        row["followers_spotify"],
        row["artist"],
        fontsize=12,
        color="black",
        alpha=0.8,
    )
    t.set_clip_on(True)
    texts.append(t)

# Adjust labels with constraints
adjust_text(
    texts,
    ax=ax,
    expand_text=(1.05, 1.05),
    expand_points=(1.05, 1.05),
    force_text=0.3,
    force_points=0.2,
    only_move={"points": "y", "text": "y"},
    arrowprops=dict(arrowstyle="-", color="gray", lw=0.5),
    lim=100,
    precision=0.01,
)

# Titles and labels
plt.title("Spotify listeners vs followers of artists performing at 70000 tons of metal 2025")
plt.xlabel("Listeners (log scale)")
plt.ylabel("Followers (log scale)")

plt.tight_layout()
plt.show()

# %%
