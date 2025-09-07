# %% HEADER
# A collection of functions to get artist data from various sources

# %% IMPORTS
import requests

# %% CONFIGS
MB_ROOT = 'https://musicbrainz.org/ws/2/'
LASTFM_ROOT = 'https://ws.audioscrobbler.com/2.0/'

# %% FUNCTIONS
def get_artist(artist_name: str) -> dict:
    q = f'{MB_ROOT}artist/?query=name:"{artist_name}"&fmt=json'
    resp = requests.get(q)
    resp.json()

    # Get info for exact match or first result
    try:
        artist_info = [
            artist 
            for artist 
            in resp.json()['artists']
            if artist['name'] == artist_name
        ][0]
    except IndexError:
        artist_info = resp.json()['artists'][0]
        print(f"No artist found with exact name {artist_name}. Instead found artist with name {artist_info['name']}.")
        
    return artist_info

def get_artist_mbid(artist_name: str):
    artist_info = get_artist(artist_name)
    return artist_info['id']

def get_similar_artists(artist_name: str, lastfm_api_key: str, limit: int=100) -> list:
    mbid = get_artist_mbid(artist_name)
    q = f'{LASTFM_ROOT}?method=artist.getsimilar&mbid={mbid}&api_key={lastfm_api_key}&limit={limit}&format=json'
    resp = requests.get(q)
    similar_artists = resp.json()['similarartists']['artist']

    # Clean up a little bit - leave only needed keys and fix types
    similar_artists = [
        {
            'name': artist.get('name'),
            'mbid': artist.get('mbid'),
            'similarity': float(artist.get('match')),
            'url': artist.get('url')
            } 
        for artist 
        in similar_artists
        ]
    return similar_artists

def get_lastfm_listener_count(artist_name: str, lastfm_api_key: str) -> int:
    # Skip using mbid, it does not return reliable results for arist names like "Be'lakor"
    q = f'{LASTFM_ROOT}?method=artist.getinfo&artist={artist_name}&api_key={lastfm_api_key}&format=json'
    resp = requests.get(q)
    listener_count = int(resp.json()['artist']['stats']['listeners'])
    return listener_count
