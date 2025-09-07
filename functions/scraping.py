# %% HEADER
# A collection of functions to get artist data from various sources
# TODO: Docstrings
# TODO: Basic typing

# %% IMPORTS
import requests
from .dbfuncs import db_cache
from time import sleep

# %% CONFIGS
MB_ROOT = "https://musicbrainz.org/ws/2/"
LASTFM_ROOT = "https://ws.audioscrobbler.com/2.0/"

# %% FUNCTIONS
@db_cache
def fetch(url: str, backoff: float = 1.5) -> requests.Response:
    # print(f"No cache, fetching {url}...")
    # Don't hammer the server. 1 request per second is a safe assumption
    sleep(backoff)
    return requests.get(url, timeout=30)

def get_artist_info(artist_name: str, **kwargs) -> dict:
    q = f'{MB_ROOT}artist/?query=name:"{artist_name}"&fmt=json'
    resp = fetch(q, **kwargs)
    # resp = fetch(q)
    
    # Get info for exact match or first result
    try:
        artist_info = [
            artist for artist in resp["artists"] if artist["name"] == artist_name
        ][0]
    except IndexError:
        artist_info = resp["artists"][0]
        print(
            f"No artist found with exact name {artist_name}. Instead found artist with name {artist_info['name']}."
        )
    # Don't hammer the server - MusicBrainz throttles at 1 request per second
    return artist_info

def get_artist_mbid(artist_name: str, **kwargs):
    artist_info = get_artist_info(artist_name, **kwargs)
    return artist_info["id"]

def get_similar_artists(
    artist_name: str, lastfm_api_key: str, limit: int = 100, **kwargs
) -> list:
    mbid = get_artist_mbid(artist_name)
    q = f"{LASTFM_ROOT}?method=artist.getsimilar&mbid={mbid}&api_key={lastfm_api_key}&limit={limit}&format=json"
    # resp = fetch(q)
    resp = fetch(q, **kwargs)
    similar_artists = resp["similarartists"]["artist"]

    # Clean up a little bit - leave only needed keys and fix types
    similar_artists = [
        {
            "name": artist.get("name"),
            "mbid": artist.get("mbid"),
            "similarity": float(artist.get("match")),
            "url": artist.get("url"),
        }
        for artist in similar_artists
    ]    
    return similar_artists


def get_lastfm_listener_count(artist_name: str, lastfm_api_key: str, **kwargs) -> int:
    # Skip using mbid, it does not return reliable results for arist names like "Be'lakor"
    q = f"{LASTFM_ROOT}?method=artist.getinfo&artist={artist_name}&api_key={lastfm_api_key}&format=json"
    # resp = fetch(q)
    resp = fetch(q, **kwargs)

    listener_count = int(resp["artist"]["stats"]["listeners"])
    return listener_count
