# %% HEADER
# A collection of functions to get artist data from various sources and do some
# caching and processing of the request responses.

# %% IMPORTS
import base64
from functools import cache
from time import sleep

from bs4 import BeautifulSoup
import requests

from .dbfuncs import db_cache
from .utils import get_parsed_date, ttl_cache

# %% CONSTANTS
MB_ROOT = "https://musicbrainz.org/ws/2/"
LASTFM_ROOT = "https://ws.audioscrobbler.com/2.0/"
GENIUS_ROOT = "http://api.genius.com/"


# %% FUNCTIONS
@db_cache
def fetch(url: str, backoff: float = 1.5) -> requests.Response:
    """Fetch a URL and return the response.

    With db_cache, this will either retrieve
    a cached response or fetch a new one and insert that into the database.

    Args:
        url (str): The url to request.
        backoff (float, optional): The time to wait between requests. Defaults to 1.5.

    Returns:
        requests.Response: The response.
    """
    # Don't hammer the server. 1 request per second is a safe assumption
    sleep(backoff)
    return requests.get(url, timeout=30)


def get_artist_info(artist_name: str, **kwargs) -> dict:
    """Get artist info from MusicBrainz.

    Args:
        artist_name (str): The name of the artist to get info for.

    Returns:
        dict: The artist info.
    """
    q = f'{MB_ROOT}artist/?query=name:"{artist_name}"&fmt=json'
    resp = fetch(q, **kwargs)

    # Get info for exact match if present, or return first result (which should be the closest match)
    try:
        artist_info = [
            artist for artist in resp["artists"] if artist["name"] == artist_name
        ][0]
    except IndexError:
        artist_info = resp["artists"][0]
        print(
            f"No artist found with exact name {artist_name}. Instead found artist with name {artist_info['name']}."
        )
    return artist_info


def get_artist_mbid(artist_name: str, **kwargs) -> str:
    """Get the MBID for an artist from MusicBrainz.

    Args:
        artist_name (str): The artist name.

    Returns:
        str: The MBID of the artist.
    """
    artist_info = get_artist_info(artist_name, **kwargs)
    return artist_info["id"]


def get_similar_artists(
    artist_name: str, lastfm_api_key: str, limit: int = 100, **kwargs
) -> list:
    """Get similar artist to an artist from Last.fm.

    Args:
        artist_name (str): The artist to get similar artists for.
        lastfm_api_key (str): Your Last.fm API key.
        limit (int, optional): The number of similar artists to get. Defaults to 100.

    Returns:
        list: The similar artists, along with their similarity and MBID.
    """
    mbid = get_artist_mbid(artist_name)
    q = f"{LASTFM_ROOT}?method=artist.getsimilar&mbid={mbid}&api_key={lastfm_api_key}&limit={limit}&format=json"
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
    """Get the listener count for an artist from Last.fm.

    This method explicitly uses the artist name,
    not the MBID, as the artist name is more reliable for artists with punctuation in their name, such as
    "Be'lakor".

    Args:
        artist_name (str): The artist name.
        lastfm_api_key (str): Your Last.fm API key.

    Returns:
        int: The listener count of the artist.
    """
    q = f"{LASTFM_ROOT}?method=artist.getinfo&artist={artist_name}&api_key={lastfm_api_key}&format=json"
    resp = fetch(q, **kwargs)
    try:
        listener_count = int(resp["artist"]["stats"]["listeners"])
    except KeyError:
        print(f"No listener count found for {artist_name}")
        listener_count = None
    return listener_count


def get_artist_albums(artist_name: str, **kwargs) -> list:
    """Get album releases for an artist from MusicBrainz.

    This returns the first release of each album, not necessarily the latest.

    Args:
        artist_name (str): The name of the artist.

    Returns:
        list: The album releases with some details.
    """
    mbid = get_artist_mbid(artist_name)
    q = f"{MB_ROOT}release-group?artist={mbid}&type=album&fmt=json"
    resp = fetch(q, **kwargs)

    albums = [
        {
            "artist_name": artist_name,
            "album_title": album.get("title"),
            "release_date": get_parsed_date(album.get("first-release-date")),
            "album_mbid": album.get("id"),
        }
        for album in resp["release-groups"]
        # Needs a release date
        if album.get("first-release-date")
        # No secondary types - this is likely some rerelease
        and not album.get("secondary-types")
    ]
    return albums


def get_genre_artists(genre: str, n_artists: int = 25, **kwargs) -> list:
    """Get artists from a genre from MusicBrainz.

    Args:
        genre (str): The genre to get artists for.
        n_artists (int, optional): The number of artists to get. Defaults to 25, gets cut off at 100.

    Returns:
        list: The artists.
    """
    if n_artists > 100:  # Single MusicBrainz request can only get 100 artists
        n_artists = min(n_artists, 100)
        print(f"Warning: Capping artists for genre {genre} at 100.")
    q = f'{MB_ROOT}artist/?query=tag:"{genre}"&limit={n_artists}&fmt=json'
    resp = fetch(q, **kwargs)

    artists = [
        {"name": artist["name"], "mbid": artist["id"]} for artist in resp["artists"]
    ]
    return artists


@ttl_cache(maxsize=128, ttl=3540)  # Token expires in 3600, so leave some room
def get_spotify_access_token(spotify_client_id: str, spotify_client_secret: str) -> str:
    """Get a Spotify access token.

    This function uses the Spotify client ID and secret to get an access token. The access
    token is then cached for 3540 seconds (1 hour) to avoid repeatedly requesting it.

    Args:
        spotify_client_id (str): The Spotify client ID.
        spotify_client_secret (str): The Spotify client secret.

    Returns:
        str: The access token.
    """
    auth_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(
        f"{spotify_client_id}:{spotify_client_secret}".encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    resp = requests.post(auth_url, headers=headers, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


@cache
def get_spotify_artist(
    artist_name: str, spotify_client_id: str, spotify_client_secret: str
) -> dict:
    """Get Spotify artist info.

    This function uses the Spotify client ID and secret to get artist info from Spotify.
    The access token is cached for 3540 seconds (1 hour) to avoid repeatedly requesting it.

    Args:
        artist_name (str): The name of the artist.
        spotify_client_id (str): The Spotify client ID.
        spotify_client_secret (str): The Spotify client secret.

    Returns:
        dict: The artist info or None if not found.
    """
    token = get_spotify_access_token(spotify_client_id, spotify_client_secret)
    search_url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": artist_name, "type": "artist", "limit": 1}

    resp = requests.get(search_url, headers=headers, params=params)
    resp.raise_for_status()
    artist_info = [
        artist
        for artist in resp.json()["artists"]["items"]
        if artist["name"].lower() == artist_name.lower()
    ]
    sleep(1.5)  # Sleep to avoid hammering the server
    if artist_info:
        return artist_info[0]
    else:
        return None


@cache
def get_setlists(artist: str, setlistfm_api_key: str, page: int = 1) -> dict:
    """Get setlists for an artist from Setlist.fm.

    Args:
        artist (str): The name of the artist.
        setlistfm_api_key (str): The Setlist.fm API key.
        page (int, optional): The page number. Defaults to 1.

    Returns:
        dict: The setlists with some details.
    """
    headers = {"x-api-key": setlistfm_api_key, "Accept": "application/json"}
    mbid = get_artist_mbid(artist)
    url = f"https://api.setlist.fm/rest/1.0/artist/{mbid}/setlists?p={page}"
    response = requests.get(url, headers=headers)
    sleep(1.5)  # Sleep to avoid hammering the server
    return response.json()


def get_artist_songs(
    artist: str, client_access_token: str, per_page: int = 20, page: int = 1, **kwargs
) -> dict:
    """Get songs and url to lyrics for an artist from Genius.

    NOTE: If Genius is dicking around, this might be because of it detecting a VPN. If
    so, turn off the VPN and try again.

    Args:
        artist (str): The artist to get songs for.
        client_access_token (str): The client access token.
        per_page (int, optional): The number of hits to get per page. Defaults and limited to 20.
        page (int, optional): The page to get. Defaults and minimised to 1.

    Returns:
        dict: A collection of information about the songs by the artist
    """
    # Set correct contraints on endpoint
    per_page = min(per_page, 20)
    page = max(page, 1)

    # Get Genius hits
    genius_search_url = f"{GENIUS_ROOT}search?q={artist}&per_page={per_page}&page={page}&access_token={client_access_token}"
    resp = fetch(genius_search_url, **kwargs)
    return resp


def get_genius_lyrics(url: str, **kwargs) -> list:
    """Get lyrics from a Genius song page.

    NOTE: If Genius is dicking around, this might be because of it detecting a VPN. If
    so, turn off the VPN and try again.

    This is a literal scrape of the lyrics page and will likely include some junk, such
    as a reference to the number of contributors, verse tags and whitespace. But it works

    Args:
        url (str): The url of the Genius song page.

    Returns:
        list: Each line of the lyrics, which may include some junk.
    """
    response = fetch(url, **kwargs)
    soup = BeautifulSoup(response, "html.parser")

    # Get containers with lyrics
    lyrics_containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})

    # Remove divs with annotations
    for container in lyrics_containers:
        for div in container.find_all(
            "div", attrs={"data-exclude-from-selection": "true"}
        ):
            div.decompose()  # Completely removes the tag from the tree

    # Join up the lines of each container and split again
    # This gets rid of whitespace and splits newlines
    raw_lyrics = "\n".join([
        ele.get_text(separator="\n").strip() for ele in lyrics_containers
    ]).split("\n")

    return raw_lyrics
