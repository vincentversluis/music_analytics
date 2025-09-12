# %% HEADING
# The aim of this script is to find the starting date of specific bands' tours. The input is a list 
# of bands and the output is an overview of when the tours started.
# TODO: Run this for Aephanemer

# %% IMPORTS
import pandas as pd
import setlist_fm_client
import os
from functools import cache
from math import ceil
from time import sleep
from utils import db_utils
from utils.utils import get_parsed_date

# %% INPUT
setlistfm_api_key_file = '../data/setlistfm_api_key.txt'
years_back = 10
db_path = '../data/db.sqlite3'

# %% CONFIGS
with open(setlistfm_api_key_file, 'r') as f:
    os.environ["SETLIST_FM_API_KEY"] = f.read()

# %% FUNCTIONS
@cache
def get_setlist_page(band, page):
    return setlist_fm_client.search_setlists(artist_name=band, p=page)


# %% MAIN
# Get bands
bands_df = pd.read_csv('bands.csv', delimiter=';')
bands = bands_df['Band'].to_list()
bands[:25]

# %%
# Get setlists for each band
for band in bands[:25]:
    # Start from page 1 
    page = 1

    while True:
        # Check if setlist has already been retrieved
        if db_utils.is_retrieved(db_path, band, page):
            print(f"Skipping page {page} for {band}. Already retrieved.")
            page += 1
            continue
        
        # Retrieve, but don't hammer the server (too much)
        sleep(2.5)
        resp = get_setlist_page(band, page)
        setlists = resp.json()['setlist']
        
        # Alarm bells if error
        if resp.status_code != 200:
            print(f"Error with page {page}. Status code: {resp.status_code}")
            break
        
        # Add setlists to database and mark as retrieved
        db_utils.insert_raw_setlists_into_table(db_path, setlists)
        db_utils.mark_retrieved(db_path, band, page)
        print(f"Retrieved page {page} for {band}.")
        
        # Break if current page is last page
        if page == ceil(resp.json()['total'] / 20):
            print(f"Done collecting setlists for {band}. Reached last page.")
            break
        
        # Break if earliest retrieved setlist is from before threshold year
        earliest_year = min([
            get_parsed_date(setlist['eventDate']).year 
            for setlist 
            in setlists])
        if earliest_year < arrow.now().year - years_back:
            print(f"Done collecting setlists for {band}. Reached {years_back} years back.")
            break
        
        # Next page
        page += 1
    
# %%
