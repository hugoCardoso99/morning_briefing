"""
Weather node — fetches forecast data from Open-Meteo for each configured city.
Detects severe weather conditions based on configurable thresholds.
"""

import requests
from utils.geocoding import geocode_city

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Severe weather thresholds
THRESHOLDS = {
    "rain_probability_pct": 70,
    "temp_max_c": 35,
    "temp_min_c": 5,
    "wind_speed_kmh": 50,
}


def _fetch_forecast(lat: float, lon: float, timezone: str) -> dict | None:
    """Fetch today's forecast for a single location."""
    try:
        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": ",".join([
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "windspeed_10m_max",
                    "weathercode",
                    "sunrise",
                    "sunset",
                ]),
                "current_weather": "true",
                "timezone": timezone,
                "forecast_days": 1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"[weather] Error fetching forecast: {e}")
        return None


# WMO weather code descriptions with emojis
WMO_CODES = {
    0: "☀️ Clear sky", 1: "🌤️ Mainly clear", 2: "⛅ Partly cloudy", 3: "☁️ Overcast",
    45: "🌫️ Foggy", 48: "🌫️ Depositing rime fog",
    51: "🌦️ Light drizzle", 53: "🌧️ Moderate drizzle", 55: "🌧️ Dense drizzle",
    61: "🌧️ Slight rain", 63: "🌧️ Moderate rain", 65: "🌧️💧 Heavy rain",
    71: "🌨️ Slight snow", 73: "❄️ Moderate snow", 75: "❄️❄️ Heavy snow",
    80: "🌦️ Slight rain showers", 81: "🌧️ Moderate rain showers", 82: "⛈️ Violent rain showers",
    85: "🌨️ Slight snow showers", 86: "❄️❄️ Heavy snow showers",
    95: "⛈️ Thunderstorm", 96: "⛈️🧊 Thunderstorm with slight hail", 99: "⛈️🧊 Thunderstorm with heavy hail",
}


def _detect_severe_weather(daily: dict) -> list[str]:
    """Check daily forecast against thresholds and return warnings."""
    warnings = []

    temp_max = daily.get("temperature_2m_max", [None])[0]
    temp_min = daily.get("temperature_2m_min", [None])[0]
    rain_prob = daily.get("precipitation_probability_max", [None])[0]
    wind_max = daily.get("windspeed_10m_max", [None])[0]

    if temp_max is not None and temp_max > THRESHOLDS["temp_max_c"]:
        warnings.append(f"Extreme heat: {temp_max}°C expected")
    if temp_min is not None and temp_min < THRESHOLDS["temp_min_c"]:
        warnings.append(f"Cold warning: low of {temp_min}°C expected")
    if rain_prob is not None and rain_prob > THRESHOLDS["rain_probability_pct"]:
        warnings.append(f"High rain probability: {rain_prob}%")
    if wind_max is not None and wind_max > THRESHOLDS["wind_speed_kmh"]:
        warnings.append(f"Strong winds: up to {wind_max} km/h")

    return warnings


def weather_node(state) -> dict:
    """Fetch weather forecasts for all configured cities."""
    cities = state.cities
    weather_results = {}

    for city_name in cities:
        geo = geocode_city(city_name)
        if geo is None:
            weather_results[city_name] = {"error": f"Could not geocode '{city_name}'"}
            continue

        raw = _fetch_forecast(geo["latitude"], geo["longitude"], geo["timezone"])
        if raw is None:
            weather_results[city_name] = {"error": f"Could not fetch forecast for '{city_name}'"}
            continue

        daily = raw.get("daily", {})
        current = raw.get("current_weather", {})
        weather_code = current.get("weathercode", 0)

        weather_results[city_name] = {
            "location": geo,
            "current": {
                "temperature": current.get("temperature"),
                "windspeed": current.get("windspeed"),
                "description": WMO_CODES.get(weather_code, "Unknown"),
            },
            "daily": {
                "temp_max": daily.get("temperature_2m_max", [None])[0],
                "temp_min": daily.get("temperature_2m_min", [None])[0],
                "rain_probability": daily.get("precipitation_probability_max", [None])[0],
                "wind_max": daily.get("windspeed_10m_max", [None])[0],
                "sunrise": daily.get("sunrise", [None])[0],
                "sunset": daily.get("sunset", [None])[0],
            },
            "severe_warnings": _detect_severe_weather(daily),
        }

    return {"weather": weather_results}
