# %% HEADER
# Scrape concerts from concerts-metal.com.

# %% IMPORTS
import json
import re
from time import sleep

from mullpy import switch_mullvad_random_server
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
    re.IGNORECASE,
)
regex_history = re.compile(
    r'<a\s+title="[^"]*?History[^"]*?"\s+href="(?P<history_url>f-[^"]+?)"',  # Mention of history and url
    re.IGNORECASE,
)

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
    festival_elements = driver.find_elements(By.CLASS_NAME, "d-xl-none")

    for festival_element in festival_elements:
        festival_html_text = festival_element.get_attribute("innerHTML")

        # Quick and dirty parsing (I know, regex is nice, but this is apparently more robust)
        # Find mouse over text which contains details
        festival_details = festival_html_text.split('<a title="')[1].split('" href="')[
            0
        ]
        name, *_, city, country, date = festival_details.split(" - ")

        url = festival_html_text.split('" href="')[1].split('"><b>')[0]

        # Use regexes for history and next event (this is more robust than quick and dirty parsing)
        history = regex_history.search(festival_html_text)
        history_url = history.group("history_url") if history else None

        next_event = regex_next_event.search(festival_html_text)
        next_url = next_event.group("next_url") if next_event else None

        festival_info = {
            "name": name,
            "city": city,
            "country": country,
            "date": date,
            "url": url,
            "history_url": history_url,
            "next_url": next_url,
        }
        festivals.append(festival_info)

##### Scrape festival details #####
# Counter for switching Mullvad relays
i = 0
# Get all artists at found festivals
for festival in tqdm(festivals, desc="Getting artists at festivals"):
    # If already scraped, skip
    if festival.get("artists"):
        continue

    # Switch to a random Mullvad relay every 100 requests
    i += 1
    if i % 100 == 0:
        switch_mullvad_random_server(noisy=True)
        sleep(5)  # Wait for relay to switch
        i = 0

    # Go to festival page and scrape
    driver.get(f"https://en.concerts-metal.com/{festival['url']}")
    sleep(2)  # Wait for page to load and don't hammer the server

    # Get each <tr> in the table
    artists_elements = driver.find_elements(By.XPATH, "//tr")

    artists = []
    for artist_element in artists_elements:
        artist_html_text = artist_element.get_attribute("outerHTML")

        # Get artist url
        try:
            artist_url = artist_html_text.split('" href="')[1].split('">')[0]
            if not artist_url.startswith("g-"):
                artist_url = None
        except IndexError:
            artist_url = None

        # Get artist genre
        try:
            artist_genre = artist_html_text.split('"> - ')[1].split("</div>")[0]
        except IndexError:
            artist_genre = None

        # Get artist name
        try:
            # Non bold text (non headliner)
            artist_name = artist_html_text.split("</a>")[0].split(">")[-1]
            # Headliner
            if not artist_name:
                artist_name = artist_html_text.split("</b>")[0].split(">")[-1]
            # Band without a site
            if not artist_url and not artist_name:
                artist_name = artist_html_text.split("</font>")[0].split('">')[-1]
            # Scraped something that is not a band
            if artist_name == "&nbsp;</td></tr>":
                artist_name = None
        except IndexError:
            artist_name = None

        artist = {"url": artist_url, "genre": artist_genre, "name": artist_name}
        # At least have genre and artist name
        # Only take artists in once to avoid duplicates
        if artist_genre and artist_name and artist not in artists:
            artists.append(artist)

    festival["artists"] = artists

driver.quit()

# Store for later use
with open("../../data/festivals.json", "w", encoding="utf-8") as f:
    json.dump(festivals, f)

# %%
