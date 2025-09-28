# %% HEADING
# The aim of this script is collecting data from Encyclopaedia Metallum and Last.fm
# to compare the platforms by which artists are suggested as similar to a specific artist.

# %% IMPORTS
# Set paths
from time import sleep

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

# %% INPUT
artists = ["Aephanemer", "Dark Tranquillity", "Metallica"]
lastfm_similar_n = 666  # Number of similar artists to get from Last.fm

# %% CONFIGS
url_base = "https://www.metal-archives.com/"

# %% GET DATA
# Start browser for Metallum - Last.fm just uses an API
driver = webdriver.Chrome()

similar_artists_metallum = []
for artist in tqdm(artists, desc="Getting artists"):
    # Go to artist page
    search_url = f"{url_base}search?searchString={artist.lower()}&type=band_name"
    driver.get(search_url)
    sleep(2)  # Wait for page to load and don't hammer the server

    # Get all tabs
    tabs_element = driver.find_element(By.XPATH, '//*[@id="band_tabs"]/ul')
    tabs = tabs_element.find_elements(By.XPATH, ".//li")

    # Check if similar artists exist - if so, click
    if "Similar Artists" not in [tab.text for tab in tabs]:
        print(f"0001: Similar artists tab not found for {artist}")
        break
    for tab in tabs:
        if tab.text == "Similar Artists":
            tab.click()
            sleep(2)
            break

    # Break if no similar artists found
    if driver.find_elements(By.XPATH, '//*[@id="no_artists"]'):
        print(f"0002: Similar artists tab not found for {artist}")
        break

    # Get more similar artists if available
    if element := driver.find_element(By.XPATH, '//*[@id="show_more"]/a'):
        element.click()
        sleep(2)

    # Get similar artists table and parse
    similar_artists_html = driver.find_element(
        By.XPATH, '//*[@id="artist_list"]/tbody'
    ).get_attribute("innerHTML")
    soup = BeautifulSoup(similar_artists_html, "html.parser")

    # Collect data by row
    for tr in soup.find_all("tr", id=lambda x: x and x.startswith("recRow_")):
        tds = tr.find_all("td")
        similar_artist = tds[0].get_text(strip=True)
        artist_url = tds[0].find("a")["href"]
        country = tds[1].get_text(strip=True)
        genre = tds[2].get_text(strip=True)
        similarity_score = tds[3].get_text(strip=True)

        similar_artists_metallum.append({
            "artist": artist,
            "similar_artist": similar_artist,
            "url": artist_url,
            "country": country,
            "genre": genre,
            "score": int(similarity_score),
        })

# Close browser
driver.quit()

# Save to csv for later use
pd.DataFrame(similar_artists_metallum).to_csv(
    "../../data/artists_platform_similarity_metallum.csv", index=False
)

# %%
