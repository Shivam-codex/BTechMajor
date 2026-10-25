"""
High-Accuracy Reverse Geocoding Service using OpenStreetMap Nominatim.
Strictly adheres to OSM Nominatim Usage Policy:
1. Custom descriptive User-Agent.
2. Max 1 request per second rate limiting.
3. Thread-safe in-memory caching keyed by rounded coordinates (~11m precision).
4. Zero transmission of confidential citizen data (strictly lat/lon floats only).
5. OpenStreetMap attribution included in results.
"""

import time
import json
import logging
import threading
import urllib.request
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("smart_city_backend")

# OpenStreetMap attribution string
OSM_ATTRIBUTION = "© OpenStreetMap contributors"

# Thread-safe in-memory cache: (round(lat, 4), round(lon, 4)) -> dict
_GEO_CACHE: Dict[Tuple[float, float], Dict[str, Any]] = {}
_CACHE_LOCK = threading.Lock()

# Rate limiting lock and timestamp
_RATE_LIMIT_LOCK = threading.Lock()
_LAST_REQUEST_TIME: float = 0.0
_MIN_REQUEST_INTERVAL: float = 1.05  # Nominatim policy: at most 1 request per second


def reverse_geocode_coordinates(
    lat: float,
    lon: float,
    timeout_sec: float = 3.0,
) -> Dict[str, Any]:
    """
    Reverse geocodes WGS84 coordinates to a human-readable civic address.
    Complies with OSM Nominatim usage policy with rate-limiting and caching.
    
    Returns dict:
    {
        "success": bool,
        "address": str,
        "latitude": float,
        "longitude": float,
        "attribution": str,
        "cached": bool,
    }
    """
    global _LAST_REQUEST_TIME

    if lat is None or lon is None:
        return {
            "success": False,
            "address": "",
            "latitude": None,
            "longitude": None,
            "attribution": OSM_ATTRIBUTION,
            "cached": False,
        }

    # Normalize to 4 decimal places (~11.1 meters) for effective spatial caching
    cache_key = (round(float(lat), 4), round(float(lon), 4))

    with _CACHE_LOCK:
        if cache_key in _GEO_CACHE:
            cached_val = dict(_GEO_CACHE[cache_key])
            cached_val["cached"] = True
            return cached_val

    # Rate limiting: wait if less than 1.05s since previous request
    with _RATE_LIMIT_LOCK:
        now = time.time()
        elapsed = now - _LAST_REQUEST_TIME
        if elapsed < _MIN_REQUEST_INTERVAL:
            time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
        _LAST_REQUEST_TIME = time.time()

    address_str = f"Lat: {lat:.5f}, Lon: {lon:.5f}"
    success = False

    try:
        # Nominatim reverse geocode endpoint - only sending lat and lon (zero confidential data)
        url = (
            f"https://nominatim.openstreetmap.org/reverse"
            f"?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SmartCityComplaintManagementSystem/1.0 (academic-project; https://github.com/Shivam-codex/BTechMajor)",
                "Accept-Language": "en,mr,hi",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            display_name = data.get("display_name")
            if display_name:
                address_str = display_name
                success = True
    except Exception as exc:
        logger.debug("Nominatim reverse geocoding skipped/failed: %s", exc)

    result = {
        "success": success,
        "address": address_str,
        "latitude": float(lat),
        "longitude": float(lon),
        "attribution": OSM_ATTRIBUTION,
        "cached": False,
    }

    # Cache positive result
    with _CACHE_LOCK:
        if len(_GEO_CACHE) > 500:
            # Simple eviction if cache exceeds 500 entries
            _GEO_CACHE.clear()
        _GEO_CACHE[cache_key] = result

    return result
