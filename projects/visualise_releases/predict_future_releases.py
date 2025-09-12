# %% HEADING
# The aim of this script is to predict when a band will release a new album. No fancy
# modelling is used, just some simple metrics and visualisation.

# TODO: Docstrings
# TODO: Move stuff to functions
# TODO: Add stuff to README.md
# TODO: Leave sleeps for requests function

# %% IMPORTS
# Set paths
from pathlib import Path
import sys

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # adjust as needed
sys.path.append(str(PROJECT_ROOT))

from pprint import pprint
# import xmltodict
import requests
import pandas as pd
from time import sleep
# from utils.utils import get_parsed_date

# %% INPUTS
# db_path = '../data/db.sqlite3'
bands_path = '../../data/bands.csv'
# mbroot = 'https://musicbrainz.org/ws/2/'

# %% CONFIGS

# %% FUNCTIONS
def get_artist(artist_name):
    q = f'{mbroot}artist/?query=name:{artist_name}&fmt=json'
    resp = requests.get(q)
    # Get info for exact match
    artist_info = [
        artist 
        for artist 
        in xmltodict.parse(resp.content)['metadata']['artist-list']['artist'] 
        if artist['name'] == artist_name
    ][0]
    return artist_info

def get_albums(artist_id):
    q = f'{mbroot}release-group?artist={artist_id}&type=album&fmt=json'
    resp = requests.get(q)
    albums = [
        release
        for release
        in xmltodict.parse(resp.content)['metadata']['release-group-list']['release-group']
        if not release.get('secondary-type-list')
    ]
    return albums

# %% GET DATA
# Get bands
bands_df = pd.read_csv(bands_path, delimiter=';')
bands = bands_df['Band'].to_list()


# %%
for band in bands[:25]:
    
artist_info = get_artist(band)

# Insert artist info into database
print(artist_info)

artist_id = artist_info['@id']
albums = get_albums(artist_id)

# Insert albums into database
[
    release['title']
    for release 
    in albums
]


# %%

# %%

# %%

#########################################################

# %% IMPORTS
import pandas as pd
import setlist_fm_client
import os
import arrow
from dateutil import parser
from functools import cache
from math import ceil
from time import sleep
import db_utils

# %% INPUT
setlist_api_key_file = 'api_key.txt'
years_back = 10
db_path = 'db.sqlite3'

# %% CONFIGS
with open(setlist_api_key_file, 'r') as f:
    os.environ["SETLIST_FM_API_KEY"] = f.read()

# %% FUNCTIONS
@cache
def get_setlist_page(band, page):
    return setlist_fm_client.search_setlists(artist_name=band, p=page)

def get_parsed_date(date):
    date = parser.parse(date)
    date = arrow.get(date)
    return date

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
