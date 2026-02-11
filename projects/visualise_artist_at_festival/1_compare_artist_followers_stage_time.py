"""The aim of this script is to make a visualisation of followers of artists performing at 70K tons of metal.

Add the largest stage each artist performed at to the plot to provide some context.
"""

# %% IMPORTS
import datetime

from adjustText import adjust_text
from matplotlib import ticker
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# %% INPUTS
year = 2026


# %% FUNCTIONS
def time_to_continuous(t: datetime.time) -> float:
    """Convert time to continuous hour scale.
    
    Starting at 10.0 for 10:00, counting through 00:00, so that 00:00 is 24.0, 
    01:30 is 25.5, etc.

    Args:
        t (datetime.time): The time to convert.

    Returns:
        float: The converted time in a continuous hour scale.
    """    
    h = t.hour + t.minute / 60
    return h if h >= 10 else h + 24  # after midnight → next day


# %% GET DATA
# Load from csv to avoid time-consuming API calls
df = pd.read_csv(f"../../data/artists_70K_{year}_abt.csv", sep=";")

# %% PREP DATA
# Convert to datetime.time if needed
df["time_largest"] = pd.to_datetime(df["time_largest"], format="%H:%M").dt.time

# Convert to continuous hour scale
df["time_cont"] = df["time_largest"].apply(time_to_continuous)

# Safety for log scales (at least 1 follower)
df = df[df["followers_spotify"] >= 1]

# %% VISUALISE
sns.set(style="whitegrid")
plt.figure(figsize=(12, 12))

# Add podium colour if column exists
if "podium_largest" in df.columns:
    ax = sns.scatterplot(
        data=df,
        x="time_cont",
        y="followers_spotify",
        hue="podium_largest",
        palette="tab10",
        s=30,
        linewidth=0,
    )
else:
    ax = sns.scatterplot(
        data=df,
        x="time_cont",
        y="followers_spotify",
        color="black",
        s=30,
        linewidth=0,
    )

# Axes
ax.set_yscale("log")
ax.yaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=10))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{int(y):,}"))
ax.grid(True, which="both", linestyle=":", linewidth=0.5)

# Custom ticks from 10:00 to 05:00 next day
xticks = [h for h in range(10, 31)]  # 10 → 30
xtick_labels = [
    f"{h:02d}:00" if h < 24 else f"{h-24:02d}:00"
    for h in xticks
]
ax.set_xticks(xticks)
ax.set_xticklabels(xtick_labels, rotation=45)

# Labels and possible clipping
texts = []
for _, row in df.iterrows():
    t = ax.text(
        row["time_cont"] * 1.002,
        row["followers_spotify"] * 1.01,
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
    autoalign='y',
    arrowprops=dict(arrowstyle="-", color="gray", lw=0.5),
    lim=300,
    precision=0.02,
)

# Titles and labels
plt.title(f"Spotify followers vs. performance time at 70000 Tons of Metal {year}")
plt.xlabel("Performance time")
plt.ylabel("Followers (log scale)")

# X limits: 10:00 → 05:00 next day
ax.set_xlim(9.3, 30.2)

# Add legend for stage if column exists
if "podium_largest" in df.columns:
    ax.legend(title="Largest stage", loc="lower right")

plt.tight_layout()
plt.show()

# %%
