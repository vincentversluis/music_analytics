# %% HEADING
# The aim of this script is to predict when a band will release a new album. No fancy
# modelling is used, just some simple metrics and visualisation.

# %% IMPORTS
import re

import arrow
import matplotlib.dates as mdates
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from functions.scraping import get_artist_albums

# %% INPUTS
years_backwards_timeline = 15  # How many years backwards to plot
years_forwards_timeline = 8  # How many years forwards to plot
recency_threshold = 10  # How many years back last release must be to be included

# %% GET DATA
# Get bands from csv (or any other source)
bands_path = "../../data/bands.csv"
artists_df = pd.read_csv(bands_path, delimiter=";")
artists = artists_df["Band"].to_list()[:25]  # Just the first so many

# Get releases for a number of artists
releases = {}
for artist in artists:
    # Get releases and sort by date
    albums = get_artist_albums(artist)

    # Remove some likely rereleases. This can usually be found by filtering the title
    # of the release and is a best effort to remove rereleases
    remove_types = ["instrumental", "revisited"]
    albums = [
        album
        for album in albums
        if not any(
            re.search(
                rf".*\s.*\b{remove_type}\b.*", album.get("album_title"), re.IGNORECASE
            )
            for remove_type in remove_types
        )
    ]

    # Keep only first release of each album name
    earliest_albums = {}
    for album in albums:
        title = album["album_title"]
        date = album["release_date"]
        if (
            title not in earliest_albums
            or date < earliest_albums[title]["release_date"]
        ):
            earliest_albums[title] = album
    albums = list(earliest_albums.values())

    # Only bother with artists with more than one release
    if len(albums) <= 1:
        print(f"0 or 1 releases for {artist}, skipping")
        continue

    # Only bother with artist that had a recent enough release
    if (
        max([album["release_date"] for album in albums])
        < arrow.now().shift(years=-recency_threshold).datetime
    ):
        print(f"Recency threshold not met for {artist}, skipping")
        continue

    # Calculate median and average time between releases
    release_dates = [album["release_date"] for album in albums]
    release_dates.sort()

    # Base prediction on last 5 releases
    last_releases = release_dates[-5:]

    # Calculate metrics of release times
    minimum = np.min([
        last_releases[i + 1] - last_releases[i] for i in range(len(last_releases) - 1)
    ]).days
    maximum = np.max([
        last_releases[i + 1] - last_releases[i] for i in range(len(last_releases) - 1)
    ]).days
    median = np.median([
        last_releases[i + 1] - last_releases[i] for i in range(len(last_releases) - 1)
    ]).days
    average = np.mean([
        last_releases[i + 1] - last_releases[i] for i in range(len(last_releases) - 1)
    ]).days

    # Calculate expected next release date
    next_release_minimum = max(last_releases).shift(days=minimum)
    next_release_maximum = max(last_releases).shift(days=maximum)
    next_release_median = max(last_releases).shift(days=median)
    next_release_average = max(last_releases).shift(days=average)
    next_release_prediction = max(last_releases).shift(days=np.mean([median, average]))

    # Only bother with artists that have an expected release relatively soon
    if (
        next_release_prediction
        > arrow.now().shift(years=years_forwards_timeline).datetime
    ):
        print(f"Next release prediction too far in the future for {artist}, skipping")
        continue

    # Add to releases
    releases[artist] = {
        "release_dates": release_dates,
        "release_count": len(release_dates),
        "minimum_release_time": minimum,
        "maximum_release_time": maximum,
        "median_release_time": median,
        "average_release_time": average,
        "next_release_median": next_release_median,
        "next_release_average": next_release_average,
        "next_release_minimum": next_release_minimum,
        "next_release_maximum": next_release_maximum,
        "next_release_prediction": next_release_prediction,
    }

# Sort by next_release_prediction
releases = dict(
    sorted(releases.items(), key=lambda item: item[1]["next_release_prediction"])
)

# %% PLOTTING
# Prepare the plot
sns.set(style="whitegrid")

height = len(releases) * 0.2
fig, ax = plt.subplots(figsize=(12, height))

# Vertical position for each artist
artist_positions = {artist: i for i, artist in enumerate(releases.keys())}

# Plot each artist's timeline
for artist, info in releases.items():
    y = artist_positions[artist]
    dates = [dt.datetime for dt in info["release_dates"]]

    # Plot release dates and lines
    ax.plot(dates, [y] * len(dates), "o-", color="black", linewidth=1, markersize=5)

    # Plot expected next release prediction range
    dates = [
        dt.datetime
        for dt in [info["next_release_minimum"], info["next_release_maximum"]]
    ]
    ax.plot(dates, [y] * len(dates), "o", color="silver", markersize=5)
    ax.plot(dates, [y] * len(dates), "--", color="grey", linewidth=1)

    # Plot expected date
    ax.plot(
        info["next_release_prediction"].datetime, y, "o", color="dimgrey", markersize=5
    )

    # Add label to prediction
    # midpoint = arrow.get(info['next_release_prediction'].float_timestamp).datetime
    prediction = info["next_release_prediction"].datetime
    ax.text(
        prediction, y + 0.1, prediction.strftime("%b %Y"), fontsize=9, color="black"
    )

# Add vertical line for current date
now = arrow.now().datetime
ax.axvline(now, color="darkgrey", linestyle="-", linewidth=1)

# Limit x-axis to a smaller window
start_date = arrow.now().shift(years=-years_backwards_timeline).datetime
end_date = arrow.now().shift(years=years_forwards_timeline).datetime
ax.set_xlim(start_date, end_date)

# Formatting
ax.set_yticks(list(artist_positions.values()))
ax.set_yticklabels(list(artist_positions.keys()))
ax.yaxis.grid(False)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.grid(True, color="lightgray", linestyle="--", linewidth=0.5)
plt.xticks(rotation=45)

# Custom legend handles
release_marker = mlines.Line2D(
    [], [], color="black", marker="o", linestyle="None", markersize=6, label="Release"
)
expected_marker = mlines.Line2D(
    [],
    [],
    color="dimgrey",
    marker="o",
    linestyle="None",
    markersize=6,
    label="Expected next release date",
)
range_marker = mlines.Line2D(
    [],
    [],
    color="silver",
    marker="o",
    linestyle="None",
    markersize=6,
    label="Expected next release range",
)
current_line = mlines.Line2D(
    [], [], color="darkgrey", linestyle="-", linewidth=1, label="Current Date"
)

# Add legend to plot
ax.legend(
    handles=[release_marker, expected_marker, range_marker, current_line],
    loc="lower right",
)

# Finishing up
plt.title("Historic album releases and expected next release")
plt.tight_layout()
plt.show()

# %%
