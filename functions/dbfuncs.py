# %% HEADER
# A collection of functions to work with the database.


# %% IMPORTS
import sqlite3
import functools
import json
import base64
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

# %%
def _detect_format(content_type: Optional[str]) -> str:
    if not content_type:
        return "text"
    ct = content_type.lower()
    if "json" in ct:
        return "json"
    if "xml" in ct:
        return "xml"
    if ct.startswith("text/"):
        return "text"
    return "bytes"

def _serialize_result(result, content_type: Optional[str], encoding: Optional[str]) -> Tuple[str, str]:
    """
    Returns (body_str, format_tag).
    body_str is str (UTF-8 text) or base64 string when format='bytes'.
    """
    # If user returned a Response, pull from it
    if isinstance(result, requests.Response):
        ct = result.headers.get("Content-Type", content_type)
        enc = result.encoding or encoding
        fmt = _detect_format(ct)
        if fmt == "bytes":
            body_str = base64.b64encode(result.content).decode("ascii")
        else:
            # use .text to respect encoding
            body_str = result.text
        return body_str, fmt

    # If user returned a dict/list -> treat as JSON
    if isinstance(result, (dict, list)):
        return json.dumps(result), "json"

    # If bytes -> store base64
    if isinstance(result, (bytes, bytearray)):
        return base64.b64encode(bytes(result)).decode("ascii"), "bytes"

    # Fallback to text
    return str(result), "json" if (content_type and "json" in content_type.lower()) else "text"

def _deserialize_to_object(body: str, fmt: str):
    if fmt == "json":
        return json.loads(body)
    if fmt == "xml":
        return ET.fromstring(body)
    if fmt == "text":
        return body
    if fmt == "bytes":
        return base64.b64decode(body)
    # Safe fallback
    return body

def _rebuild_response(request_url: str, body: str, fmt: str, status: Optional[int], headers_json: Optional[str], encoding: Optional[str]) -> requests.Response:
    r = requests.Response()
    # content
    if fmt == "bytes":
        content = base64.b64decode(body)
    else:
        content = (body if isinstance(body, bytes) else body.encode(encoding or "utf-8", errors="replace"))
    r._content = content
    r.status_code = status or 200
    r.url = request_url
    r.encoding = encoding
    r.headers = requests.structures.CaseInsensitiveDict(json.loads(headers_json) if headers_json else {})
    return r

def db_cache(func):
    """ Decorator to cache requests to a database.
    Caches by (func_name, request) where 'request' is the first positional arg.
    Control flags (optional, do not affect request signature):
      - force_refresh: bool = False  -> bypass cache and refetch
      - return_as: 'auto'|'response'  -> 'auto' returns parsed object; 'response' returns a requests.Response
    """
    @functools.wraps(func)
    def wrapper(request, *args, force_refresh: bool = False, return_as: str = "auto", **kwargs):
        fname = func.__name__

        if not force_refresh:
            conn = sqlite3.connect("../data/databases/requests_cache.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT body, format, content_type, encoding, status_code, headers FROM cache WHERE request=?",
                (request,),
            )
            row = cursor.fetchone()
            if row:
                body, fmt, content_type, encoding, status_code, headers_json = row
                if return_as == "response":
                    return _rebuild_response(request, body, fmt, status_code, headers_json, encoding)
                return _deserialize_to_object(body, fmt)

        # Miss or forced refresh → call underlying function
        result = func(request, *args, **kwargs)

        # Gather HTTP details when result is a Response
        content_type = None
        encoding = None
        status_code = None
        headers_json = None

        if isinstance(result, requests.Response):
            content_type = result.headers.get("Content-Type")
            encoding = result.encoding
            status_code = int(result.status_code)
            headers_json = json.dumps(dict(result.headers))

        # Normalize result to storable form
        body, fmt = _serialize_result(result, content_type, encoding)

        # Upsert into cache
        cursor.execute("""
            INSERT OR REPLACE INTO cache
            (request, func_name, body, format, content_type, encoding, status_code, headers, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (request, fname, body, fmt, content_type, encoding, status_code, headers_json))
        conn.commit()

        # Return the appropriate Python object
        if return_as == "response":
            return _rebuild_response(request, body, fmt, status_code, headers_json, encoding)
        return _deserialize_to_object(body, fmt)

    return wrapper

@db_cache
def fetch(url: str):
    # You can return a Response...
    print(f"No cache, fetching {url}...")
    return requests.get(url, timeout=30)

MB_ROOT = "https://musicbrainz.org/ws/2/"

def get_artist(artist_name: str, force_refresh=False) -> dict:
    q = f'{MB_ROOT}artist/?query=name:"{artist_name}"&fmt=json'
    resp = fetch(q)
    
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
    # ! Wait for a bit to avoid hammering the server
    return artist_info

def get_artist_mbid(artist_name: str):
    artist_info = get_artist(artist_name)
    return artist_info["id"]

LASTFM_ROOT = "https://ws.audioscrobbler.com/2.0/"


def get_similar_artists(
    artist_name: str, lastfm_api_key: str, limit: int = 100
) -> list:
    mbid = get_artist_mbid(artist_name)
    q = f"{LASTFM_ROOT}?method=artist.getsimilar&mbid={mbid}&api_key={lastfm_api_key}&limit={limit}&format=json"
    resp = fetch(q)
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


def get_lastfm_listener_count(artist_name: str, lastfm_api_key: str) -> int:
    # Skip using mbid, it does not return reliable results for arist names like "Be'lakor"
    q = f"{LASTFM_ROOT}?method=artist.getinfo&artist={artist_name}&api_key={lastfm_api_key}&format=json"
    resp = fetch(q)
    listener_count = int(resp["artist"]["stats"]["listeners"])
    return listener_count

# get_artist_mbid("Aephanemer")
get_lastfm_listener_count("The Halo Effect", lastfm_api_key="8d188391c9c4145d1c5f64a2d1189d48")
get_similar_artists("The Halo Effect", lastfm_api_key="8d188391c9c4145d1c5f64a2d1189d48")

# %%
# Get the contents of table 'cache' in the database
# and print them out
conn = sqlite3.connect("../data/databases/requests_cache.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM cache")
rows = cursor.fetchall()
conn.close()
for row in rows:
    print(row)
# %%
