# %% HEADING
# Get data from Setlist.fm and save to csv

# %% IMPORTS
import json
from math import ceil

import arrow
import pandas as pd
from tqdm import tqdm

from functions.scraping import get_setlists
from functions.utils import get_parsed_date

# %% INPUT
years_back = 10

# %% CONFIGS
setlistfm_api_key_path = "../../data/credentials/setlistfm_api_key.txt"
with open(setlistfm_api_key_path, encoding="utf-8") as f:
    setlistfm_api_key = f.read()

# %% GET DATA
# Get bands from csv (or any other source)
bands_path = "../../data/bands.csv"
artists_df = pd.read_csv(bands_path, delimiter=";")
artists = artists_df["Band"].to_list()[:30]  # Just the first so many

# Collect setlists
setlists = []
for artist in tqdm(artists, desc="Getting setlists"):
    page = 1  # Start from page 1
    while True:
        artist_setlists = get_setlists(artist, setlistfm_api_key, page=page)
        setlists.extend(artist_setlists["setlist"])

        # Break if current page is last page
        if page == ceil(artist_setlists["total"] / 20):
            break

        # Break if earliest retrieved setlist is from before threshold year
        earliest_year = min([
            get_parsed_date(setlist["eventDate"]).year
            for setlist in artist_setlists["setlist"]
        ])
        if earliest_year < arrow.now().year - years_back:
            break

        page += 1

# Save to json for later use
with open("../../data/setlists.json", "w", encoding="utf-8") as f:
    json.dump(setlists, f)

# %%
