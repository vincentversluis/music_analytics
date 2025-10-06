# %% HEADER
# Scrape concerts from concerts-metal.com. This is done in three steps:
# 1) Get a list of similar artists to the one of interest on Last.fm
# 2) Get the listener count for each similar artist on Last.fm
# 3) Get the concerts on concerts-metal.com for the top X similar artists by listener count
# The results are saved to a csv file
# TODO: Header
# TODO: Note somewhere that concerts-metal.com does not list all artists, but is a convenient source
# TODO: Use association rules to find pairs of artists that are similar
# TODO: Move Mullvad stuff to its own file

# %% IMPORTS
# Set paths
from pathlib import Path
import sys

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from collections import defaultdict
import json
import random
import re
import subprocess
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

# %% INPUTS
# See header for explanation
year_start = 2022
year_end = 2025

# %% FUNCTIONS AND SUCH
regex_next_event = re.compile(
    r'next:\s*<a\s+href="(?P<next_url>concert_[^"]+?)"',  # Mention of next event and url
    re.IGNORECASE
)
regex_history = re.compile(
    r'<a\s+title="[^"]*?History[^"]*?"\s+href="(?P<history_url>f-[^"]+?)"',  # Mention of history and url
    re.IGNORECASE
)


def get_mullvad_relays() -> dict:
    """Get a dict with details of all relays in Mullvad.

    Returns:
        dict: All relays
    """    
    # Get raw text output from mullvad relay list command
    try:
        raw_text = subprocess.run(["mullvad", "relay", "list"], check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as e:
        print(f"Retrieving Mullvad relays failed with code {e.returncode}")
        print(e.stderr)
    
    # Clean ugly-ass text bits
    clean_text = raw_text.replace("Â°", "°").replace("\r", "").strip()
    lines = clean_text.splitlines()
    
    # Fill a dict with details per country, city and relay
    relays = defaultdict(lambda: defaultdict(list))
    country = city = None
    for line in lines:
        stripped = line.strip()

        # Country line: Albania (al)
        country_match = re.match(r"^([A-Za-z\s]+) \((\w{2})\)$", stripped)
        if country_match:
            country, country_code = country_match.groups()
            continue

        # City line: Tirana (tia) @ 41.32795°N, 19.81902°W
        city_match = re.match(r"^([A-Za-z\s]+) \((\w{3})\) @", stripped)
        if city_match:
            city, city_code = city_match.groups()
            continue

        # Endpoint line: al-tia-wg-003 (103.204.123.130, 2a04:27c0:0:c::f001) - WireGuard, hosted by iRegister (rented)
        endpoint_match = re.match(
            r"^(\S+) \(([\d\.]+), ([\da-fA-F:]+)\) - (\w+), hosted by ([\w\s]+) \(rented\)$", stripped
        )
        if endpoint_match:
            hostname, ip, ipv6, protocol, host = endpoint_match.groups()
            relays[country][city].append({
                "hostname": hostname,
                "ip": ip,
                "ipv6": ipv6,
                "protocol": protocol,
                "host": host
            })

    return relays


def switch_mullvad_random_relay(noisy: bool = False) -> None:
    """Switch to a random Mullvad relay.

    Args:
        noisy (bool, optional): If new relay should be printed. Defaults to False.
    """    
    relays = get_mullvad_relays()
    
    # Collect hostnames from nested structure
    hostnames = []
    for country_data in relays.values():
        for city_data in country_data.values():
            for endpoint in city_data:
                hostnames.append(endpoint["hostname"])
                
    # Pick a hostname and switch to it
    relay = random.choice(hostnames)
    if noisy:
        print(f"Switching Mullvad location to {relay}")
    try:
        # CLI equivalent of: mullvad relay set location <hostname>
        subprocess.run(["mullvad", "relay", "set", "location", relay], check=True, capture_output=True, text=True)
        # CLI equivalent of: mullvad connect
        subprocess.run(["mullvad", "connect"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Setting Mullvad location failed with code {e.returncode}")
        print(e.stderr)

switch_mullvad_random_relay()

# %%
# Get all festivals in the given years
# Start browser
driver = webdriver.Chrome()

festivals = []
for year in range(2022, year_end + 1):
    # Open concerts-metal.com page for festivals of the given year
    driver.get(f"https://en.concerts-metal.com/festivals-{year}.html")
    sleep(2)  # Wait for page to load and don't hammer the server

    # Find all festivals - this is a list of divs with class d-xl-none
    festival_elements = driver.find_elements(
            By.CLASS_NAME, "d-xl-none"
        )

    for festival_element in festival_elements:
        festival_html_text = festival_element.get_attribute('innerHTML')

        # Quick and dirty parsing (I know, regex is nice, but this is apparently more robust)
        # Find mouse over text which contains details
        festival_details = festival_html_text.split('<a title="')[1].split('" href="')[0]
        name, *_, city, country, date = festival_details.split(" - ")

        url = festival_html_text.split('" href="')[1].split('"><b>')[0]

        # Use regexes for history and next event (this is more robust than quick and dirty parsing)
        history = regex_history.search(festival_html_text)
        history_url = history.group('history_url') if history else None

        next_event = regex_next_event.search(festival_html_text)
        next_url = next_event.group('next_url') if next_event else None

        festival_info = {
            'name': name,
            'city': city,
            'country': country,
            'date': date,
            'url': url,
            'history_url': history_url,
            'next_url': next_url
        }
        festivals.append(festival_info)

driver.quit()

# %%
driver = webdriver.Chrome()

# Get all artists at found festivals
for i, festival in tqdm(enumerate(festivals[2777:]), desc="Collecting artists at festivals"):
    # Switch to a random Mullvad relay every 100 requests
    if i % 100 == 0:
        switch_mullvad_random_relay()
        sleep(5)
    
    # Go to festival page and scrape
    driver.get(f"https://en.concerts-metal.com/{festival['url']}")
    sleep(2)  # Wait for page to load and don't hammer the server

    # Get element with class="tab-pane fade show active"
    # artists_table = driver.find_element(By.XPATH, "//div[@class='tab-pane fade show active']")

    # Get each <tr> in the table
    artists_elements = driver.find_elements(By.XPATH, "//tr")

    artists = []
    for artist_element in artists_elements:
        artist_html_text = artist_element.get_attribute('outerHTML')
        
        # Get artist url
        try:
            artist_url = artist_html_text.split('" href="')[1].split('">')[0]
            if not artist_url.startswith('g-'):
                artist_url = None
        except IndexError:
            artist_url = None
            
        # Get artist genre
        try:
            artist_genre = artist_html_text.split('"> - ')[1].split('</div>')[0]
        except IndexError:
            artist_genre = None
            
        # Get artist name
        try:
            # Non bold text (non headliner)
            artist_name = artist_html_text.split('</a>')[0].split('>')[-1]
            # Headliner
            if not artist_name:
                artist_name = artist_html_text.split('</b>')[0].split('>')[-1]
            # Band without a site
            if not artist_url and not artist_name:
                artist_name = artist_html_text.split('</font>')[0].split('">')[-1]
            # Scraped something that is not a band
            if artist_name == '&nbsp;</td></tr>':
                artist_name = None
        except IndexError:
            artist_name = None
            
        artist = {
            'url': artist_url,
            'genre': artist_genre,
            'name': artist_name
        }
        # At least have genre and artist name
        # Only take artists in once to avoid duplicates
        if artist_genre and artist_name and artist not in artists:
            artists.append(artist)
            
    festival['artists'] = artists

driver.quit()

# %%
# Store for later use
with open('../../data/festivals.json', "w", encoding='utf-8') as f:
    json.dump(festivals, f)

# %%
import pandas as pd
df = pd.DataFrame(festivals)

# %%