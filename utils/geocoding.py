"""
Geocoding utility using the Open-Meteo Geocoding API.
No API key required.
"""

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def geocode_city(city_name: str) -> dict | None:
    """
    Look up a city name and return its coordinates.

    Returns:
        dict with keys: name, latitude, longitude, country, timezone
        or None if the city was not found.
    """
    try:
        resp = requests.get(
            GEOCODING_URL,
            params={"name": city_name, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if "results" not in data or len(data["results"]) == 0:
            return None

        result = data["results"][0]
        return {
            "name": result.get("name", city_name),
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "country": result.get("country", ""),
            "timezone": result.get("timezone", "Europe/Lisbon"),
        }
    except requests.RequestException as e:
        print(f"[geocoding] Error geocoding '{city_name}': {e}")
        return None
