# %% HEADER
# A collection of functions to work with the database.

# %% SET PATHS
import base64
from collections.abc import Callable
import functools
import json
import os
import sqlite3
from typing import Any
import xml.etree.ElementTree as ET

import requests

# %% CONSTANTS
# Compute the absolute path to the database file
DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(__file__)
    ),  # goes up from 'functions' to 'music_analytics'
    "data",
    "databases",
    "requests_cache.db",
)


# %% FUNCTIONS
def _detect_format(content_type: str | None) -> str:
    """Detect the format of a content type.

    Args:
        content_type (str | None): The content type to detect.

    Returns:
        str: The content type.
    """
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
    """Serialise a query result.

    Args:
        result (Any): The query result to serialise.
        content_type (str | None): The content type of the result.
        encoding (str | None): The encoding of the result.

    Returns:
        tuple: The body and format.
    """
    # If user returned a Response, pull from it
    if isinstance(result, requests.Response):
        ct = result.headers.get("Content-Type", content_type)
        fmt = _detect_format(ct)
        if fmt == "bytes":
            body_str = base64.b64encode(result.content).decode("ascii")
        else:
            # use .text to respect encoding
            body_str = result.text
        return body_str, fmt

    # Otherwise, treat as JSON or text
    if isinstance(result, (dict, list)):
        return json.dumps(result), "json"
    if isinstance(result, (bytes, bytearray)):
        return base64.b64encode(bytes(result)).decode("ascii"), "bytes"

    # Fallback to text if no other format is detected and pray
    return str(result), "json" if (
        content_type and "json" in content_type.lower()
    ) else "text"


def _deserialize_to_object(body: str, fmt: str) -> object:
    """Deserialise a body to an object.

    Args:
        body (str): The body to deserialise.
        fmt (str): The format of the body.

    Returns:
        object: The deserialised object.
    """
    match fmt:
        case "json":
            return json.loads(body)
        case "xml":
            return ET.fromstring(body)
        case "text":
            return body
        case "bytes":
            return base64.b64decode(body)
        # Safe fallback
        case _:
            return body


def _rebuild_response(
    request_url: str,
    body: str,
    fmt: str,
    status: int | None,
    headers_json: str | None,
    encoding: str | None,
) -> requests.Response:
    """Rebuild a requests.Response from a body and format.

    Args:
        request_url (str): The URL of the request.
        body (str): The body of the response.
        fmt (str): The format of the body.
        status (int | None): THe status code of the response.
        headers_json (str | None): The headers of the response as JSON.
        encoding (str | None): The encoding of the response.

    Returns:
        requests.Response: The rebuilt response.
    """
    r = requests.Response()
    # Create the content
    if fmt == "bytes":
        content = base64.b64decode(body)
    else:
        content = (
            body
            if isinstance(body, bytes)
            else body.encode(encoding or "utf-8", errors="replace")
        )
    # Add the content and other details
    r._content = content
    r.status_code = status or 200
    r.url = request_url
    r.encoding = encoding
    r.headers = requests.structures.CaseInsensitiveDict(
        json.loads(headers_json) if headers_json else {}
    )
    return r


def db_cache(func: Callable) -> Callable:
    """A decorator to cache requests to a database.

    Args:
        func (Callable): The function to decorate.

    Returns:
        Callable: The decorated function.
    """

    @functools.wraps(func)
    def wrapper(
        request: str,
        *args,
        force_refresh: bool = False,
        return_as: str = "auto",
        **kwargs,
    ) -> Any:
        """The wrapper function.

        Args:
            request (str): The request.
            force_refresh (bool, optional): Force the request to be refetched. Defaults to False.
            return_as (str, optional): The format to return the result in. Defaults to "auto".

        Returns:
            Any: The result of the request.
        """
        fname = func.__name__

        # Check if the result for this request is in the cache
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

        # No return from cache, call underlying function
        result = func(request, *args, **kwargs)

        # Gather HTTP details when result is a response
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

        # Insert into cache
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

        # Return the appropriate object
        if return_as == "response":
            return _rebuild_response(
                request, body, fmt, status_code, headers_json, encoding
            )
        return _deserialize_to_object(body, fmt)

    return wrapper
