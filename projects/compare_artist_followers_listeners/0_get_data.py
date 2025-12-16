"""The aim of this script is to collect data to investigate follower numbers of artists performing at 70K tons of metal."""

# %% IMPORTS
from time import sleep

from mullpy import switch_mullvad_random_server
import pandas as pd
from tqdm import tqdm

from functions.scraping import (
    get_spotify_followers_and_listeners,
)

# %% INPUTS
scrapes_before_vpn_switch = 10  # How many scrapes before switching VPN endpoint

# %% CONFIGS
spotify_client_id_path = "../../data/credentials/spotify_client_id.txt"
spotify_client_secret_path = "../../data/credentials/spotify_client_secret.txt"

# Get keys and such
with open(spotify_client_id_path, encoding="utf-8") as f:
    spotify_client_id = f.read()
with open(spotify_client_secret_path, encoding="utf-8") as f:
    spotify_client_secret = f.read()

# %% GET DATA
# Get bands from csv (or any other source)
bands_path = "../../data/bands_70K.csv"
artists_df = pd.read_csv(bands_path, delimiter=";")
artists = {artist: {'artist': artist.title()} for artist in artists_df["Band"].to_list()}

# %%
# Get Spotify followers and listeners for an artist
vpn_countdown = scrapes_before_vpn_switch  # Countdown to switch VPN endpoints
for _, artist in tqdm(artists.items(), desc="Getting Spotify followers and listeners"):
    # Not all artists have a Spotify page, resulting in None followers and listeners
    if followers_and_listeners := get_spotify_followers_and_listeners(
        artist["artist"], spotify_client_id, spotify_client_secret
    ):
        artist.update(followers_and_listeners)

    # Switch VPN every so many requests
    vpn_countdown -= 1
    if vpn_countdown == 0:
        switch_mullvad_random_server()
        sleep(5)  # Wait for relay to properly switch
        vpn_countdown = scrapes_before_vpn_switch  # Reset countdown

# %% SAVE DATA
# Create a csv file for manual alteration and later use
pd.DataFrame(artists.values()).to_csv("../../data/artists_70K_followers_listeners.csv", index=False)

# %%
