# %% HEADER
# Scrape concerts from concerts-metal.com. This is done in three steps:
# 1) Get a list of similar artists to the one of interest on Last.fm
# 2) Get the listener count for each similar artist on Last.fm
# 3) Get the concerts on concerts-metal.com for the top X similar artists by listener count
# The results are saved to a csv file

# %% IMPORTS
# Set paths
from pathlib import Path
import sys

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # adjust as needed
sys.path.append(str(PROJECT_ROOT))

import re
from time import sleep

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from tqdm import tqdm

from functions.scraping import get_lastfm_listener_count, get_similar_artists

# %% INPUTS
# See header for explanation
artist_name = "Aephanemer"
artists_similar_n = 100  # Number of similar artists to search for 
artists_listener_top_n = 25  # Number of artists to scrape concerts for by listener count

# %% CONFIGS
# Url to get to search for specific artists
base_url = "https://en.concerts-metal.com/bands.html"

lastfm_api_key_path = "../../data/credentials/lastfm_credentials.txt"
with open(lastfm_api_key_path, encoding="utf-8") as f:
    lastfm_api_key = f.read()

# %% FUNCTIONS AND SUCH
# Regex for parsing texts on artist page
regex_concert = re.compile(r"""
    ^                               # Start of string 
    (?P<date>.+)                    # Date in DD/MM/YYYY format, alternatively \d{2}/\d{2}/\d{4}
    \s<span\sclass="flag\sflag\-    # HTML junk
    (?P<country>.+)                 # Country code
    "></span>\s<a\stitle="          # HTML junk
    (?P<event_name>.+)              # Event name
    "\shref=".*@\s                  # HTML junk
    (?P<city>.+)                    # City
    ,\s                             # Comma separating city and venue
    (?P<venue>.+)                   # Venue
    $                               # End of string
    """,
    re.VERBOSE | re.IGNORECASE)  

# %% GET DATA
# Get bands from csv (or any other source)
# Get similar artists
similar_artists = get_similar_artists(
    artist_name=artist_name, limit=artists_similar_n, lastfm_api_key=lastfm_api_key
)

# Get listener count for each similar artist
for artist in tqdm(similar_artists, desc="Getting listener counts"):
    artist["listener_count"] = int(
        get_lastfm_listener_count(artist["name"], lastfm_api_key=lastfm_api_key)
    )

# Get first X similar artists by listener count
similar_artists.sort(key=lambda x: x["listener_count"], reverse=True)
artists = [artist['name'] for artist in similar_artists[:artists_listener_top_n]]
artists.append(artist_name)  # Add the artist of interest as a reference

# %%
# Start browser
driver = webdriver.Chrome()

concerts = []
for artist in tqdm(artists, desc="Getting concerts"):
    # Go to search page and search for the artist
    driver.get(base_url)
    sleep(2)  # Wait for page to load and don't hammer the server
    
    # Locate text input, clear and fill with artist name
    text_input = driver.find_element(By.XPATH, '//*[@id="search"]')
    driver.find_element(By.XPATH, '//*[@id="search"]').clear()
    ActionChains(driver).send_keys_to_element(text_input, artist).perform()
    driver.find_element(By.XPATH, '/html/body/main/div/div[1]/div/form/div/div[5]/input').click()
    sleep(2)  # Wait for page to load and don't hammer the server

    # Test the kind of page - if it is a selection page, choose best match and go to url
    if driver.find_elements(By.XPATH, '/html/body/main/div/h1'):
        # Check if there are actually any results at all, otherwise skip
        if not driver.find_elements(By.XPATH, '/html/body/main/div/div[2]/table/tbody'):
            print(f"No page found for {artist}, skipping")
            continue
        print(f"Redirected to a selection page for {artist}")
        
        # Get suggested matches and find best match for search
        table_html = driver.find_element(By.XPATH, '/html/body/main/div/div[2]/table/tbody').get_attribute('innerHTML')
        artist_texts = table_html.split('<tr><td><span class="flag flag-')[1:]

        artist_matches = []
        for artist_text in artist_texts:
            # Use some splitting tricks to parse the text - regex is too verbose for this
            country_childurl, *_, kind_events_n, _ = artist_text.split('</a>')
            country = country_childurl.split('"')[0]
            artist_name = country_childurl.split('.html">')[1]
            events_n = kind_events_n.split('.html">')[-1]
            url = "https://en.concerts-metal.com/" + country_childurl.split('"')[2]
            artist_matches.append({
                "country": country,
                "artist_name": artist_name,
                "events_n": int(events_n),
                "url": url
            })
            
        # Try find exact match for artist, give preference to artist with most events
        artist_matches.sort(key=lambda x: x["events_n"], reverse=True)
        try:  # Exact match
            match_exact = [match for match in artist_matches if match["artist_name"].lower() == artist.lower()][0]
            artist_url = match_exact["url"]
            print(f"Found exact match for {artist}")
        except IndexError:  # Other suggestions - use highest number of events
            artist_url = artist_matches[0]["url"]
            print(f"Did not find exact match for {artist}, using reference for {artist_matches[0]['artist_name']}")
            
        # Go!
        driver.get(artist_url)
        sleep(2)  # Wait for page to load and don't hammer the server

    # Get a plaintext version of the page - this makes parsing a million times easier
    html_text = driver.page_source
    
    # The business part is from the h2 Last events tag, up to the first <br></div> combination
    # Then split by <br>, which is the next line
    concerts_texts = html_text.split("<h2>Last events</h2>")[1].split("<br></div>")[0].split("<br>")

    # Parse the texts with a regex
    concerts.extend([
        regex_concert.match(concert_text).groupdict() 
        for concert_text 
        in concerts_texts])
    
# Close browser
driver.quit()

# Save to csv for later use
pd.DataFrame(concerts).to_csv("../../data/concerts.csv", index=False)

# %%# %% CONFIGS
concerts