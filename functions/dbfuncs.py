# %% HEADER
# A collection of functions to work with the database.
# TODO: Docstrings
# TODO: Basic typing
# TODO: Add sleeps to avoid hammering the server

# %% SET PATHS
import os
import sys


# %% IMPORTS
import base64
from collections.abc import Callable
import functools
import json
import sqlite3
from typing import Any, Optional
import xml.etree.ElementTree as ET
import requests

from config import DB_PATH


# %% FUNCTIONS
def _detect_format(content_type: str | None) -> str:
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


def _serialize_result(
    result: Any, content_type: str | None, encoding: str | None
) -> tuple:
    """
    Returns (body_str, format_tag).
    body_str is str (UTF-8 text) or base64 string when format='bytes'.
    """
    # If user returned a Response, pull from it
    if isinstance(result, requests.Response):
        ct = result.headers.get("Content-Type", content_type)
        enc = result.encoding or encoding  # ! encoding is not used
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
    return str(result), "json" if (
        content_type and "json" in content_type.lower()
    ) else "text"


def _deserialize_to_object(body: str, fmt: str) -> object:
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


def _rebuild_response(
    request_url: str,
    body: str,
    fmt: str,
    status: int | None,
    headers_json: Optional[str],
    encoding: Optional[str],
) -> requests.Response:
    r = requests.Response()
    # content
    if fmt == "bytes":
        content = base64.b64decode(body)
    else:
        content = (
            body
            if isinstance(body, bytes)
            else body.encode(encoding or "utf-8", errors="replace")
        )
    r._content = content
    r.status_code = status or 200
    r.url = request_url
    r.encoding = encoding
    r.headers = requests.structures.CaseInsensitiveDict(
        json.loads(headers_json) if headers_json else {}
    )
    return r


def db_cache(func: Callable) -> Callable:
    """Decorator to cache requests to a database.
    Caches by (func_name, request) where 'request' is the first positional arg.
    Control flags (optional, do not affect request signature):
      - force_refresh: bool = False  -> bypass cache and refetch
      - return_as: 'auto'|'response'  -> 'auto' returns parsed object; 'response' returns a requests.Response
    """

    @functools.wraps(func)
    def wrapper(
        request, *args, force_refresh: bool = False, return_as: str = "auto", **kwargs
    ):
        fname = func.__name__

        if not force_refresh:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT body, format, content_type, encoding, status_code, headers FROM cache WHERE request=?",
                (request,),
            )
            row = cursor.fetchone()
            if row:
                body, fmt, content_type, encoding, status_code, headers_json = row
                if return_as == "response":
                    return _rebuild_response(
                        request, body, fmt, status_code, headers_json, encoding
                    )
                return _deserialize_to_object(body, fmt)
            conn.commit()
            conn.close()

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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO cache
            (request, func_name, body, format, content_type, encoding, status_code, headers, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (
                request,
                fname,
                body,
                fmt,
                content_type,
                encoding,
                status_code,
                headers_json,
            ),
        )
        conn.commit()
        conn.close()

        # Return the appropriate Python object
        if return_as == "response":
            return _rebuild_response(
                request, body, fmt, status_code, headers_json, encoding
            )
        return _deserialize_to_object(body, fmt)

    return wrapper
