# %% HEADER
# Visualise when tours start

# %% IMPORTS
import arrow
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import pycountry_convert as pc

# %% INPUTS
artist_name = "Aephanemer"  # The artist to use as a reference
min_tour_concerts = 6  # Minimum number of concerts to constitute a tour
years_back = 10  # How many years back to look for concerts

# %% GET DATA
df = pd.read_csv("../../data/concerts.csv")[["artist", "date", "event_name", "country"]]

# Cast types, add continent and sort
df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
df["continent"] = df["country"].apply(
    lambda x: pc.country_alpha2_to_continent_code(x.upper())
)
df = df.sort_values(["artist", "date"], ascending=True)

# Remove events that have less than X concerts in total per artist
counts = df.groupby(["artist", "event_name"]).size().reset_index(name="count")
valid_combinations = counts[counts["count"] >= min_tour_concerts][
    ["artist", "event_name"]
]
df = df.merge(valid_combinations, on=["artist", "event_name"], how="inner")

# Get most common continent for each tour
most_common_continent = (
    df.groupby(["artist", "event_name"])["continent"]
    .agg(
        lambda x: x.mode().iloc[0]
    )  # mode() returns a Series; take the first if there's a tie
    .reset_index()
)

# Get first concert and number of events for each artist and tour
first_concert_date = (
    df.groupby(["artist", "event_name"])["date"]
    .agg(first_concert="min", events_n="count")
    .reset_index()
)

# Combine the two dataframes
df_agg = pd.merge(
    first_concert_date, most_common_continent, on=["artist", "event_name"]
)

# Only keep tours that started in the last so many years
df_agg = df_agg[df_agg["first_concert"].dt.year >= arrow.now().year - years_back]

# Replace year for 2000 for easier plotting
df_agg["first_concert"] = df_agg["first_concert"].apply(lambda x: x.replace(year=2000))

# Get starting counts for legend
continent_counts = df_agg["continent"].value_counts()

# Assign y-axis positions
artists_ordered = df_agg["artist"].drop_duplicates().tolist()
artists_ordered = [artist_name] + [a for a in artists_ordered if a != artist_name]
artists_sorted = artists_ordered[::-1]
artist_to_y = {artist: i for i, artist in enumerate(artists_sorted)}
df_agg["y_pos"] = df_agg["artist"].map(artist_to_y)

# Define color mapping and map
continent_colors = {
    "AF": "#9467bd",  # Purple
    "AN": "#e377c2",  # Pinkish
    "AS": "#ff7f0e",  # Orange
    "EU": "#1f77b4",  # Blue
    "NA": "#2ca02c",  # Green
    "OC": "#8c564b",  # Brown
    "SA": "#d62728",  # Red
}
df_agg["color"] = (
    df_agg["continent"].map(continent_colors).fillna("gray")
)  # Fallback color grey

# Create the plot
plt.figure(figsize=(12, len(artists_sorted) * 0.4))
plt.scatter(
    df_agg["first_concert"], df_agg["y_pos"], color=df_agg["color"], alpha=0.5, s=100
)

# Format x-axis to show month names
month_starts = pd.date_range(start="2000-01-01", end="2000-12-01", freq="MS")
plt.xticks(month_starts, [date.strftime("%b") for date in month_starts])

# Add some vertical lines
for date in month_starts:
    plt.axvline(date, color="gray", linestyle="--", alpha=0.3)

# Format y-axis
plt.yticks(ticks=range(len(artists_sorted)), labels=artists_sorted)
plt.title(f"Date of first concert in tour in last {years_back} years")
plt.grid(False)

# Add the legend to the plot
legend_handles = [
    mpatches.Patch(
        color=continent_colors.get(continent, "gray"), label=f"{continent} ({count})"
    )
    for continent, count in continent_counts.items()
]
plt.legend(
    handles=legend_handles,
    title="Continent (tour counts)",
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
    frameon=True,
)

plt.tight_layout()
plt.show()

# %%