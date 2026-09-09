"""
Hour 1 — WeatherGPT prototype
Fetches real weather data for a city from OpenWeatherMap.
Run: python get_weather.py

Hour 8 update: added timeouts + try/except so a bad city name, dead
internet, or a slow/odd API response returns a clean error dict instead
of crashing the whole app.
"""

import time
import requests

# 1. Paste your OpenWeatherMap API key here
API_KEY = "YOUR_API_KEY"

# Simple in-memory cache so repeated calls within CACHE_TTL_SECONDS
# reuse the same result instead of hitting the API again.
_cache = {}
CACHE_TTL_SECONDS = 300  # 5 minutes — plenty fresh for a demo

# How long to wait before giving up on a slow/dead connection (seconds)
REQUEST_TIMEOUT_SECONDS = 8


def _get_cached(key):
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return value
    return None


def _set_cached(key, value):
    _cache[key] = (value, time.time())


def get_weather(city: str) -> dict:
    """Fetch current weather + forecast text for a given city.

    Always returns a dict. On any failure (bad city, no internet, slow
    API, unexpected response shape) it returns {"error": "..."} instead
    of raising, so callers never need to wrap this in try/except.
    """
    city = (city or "").strip()
    if not city:
        return {"error": "No city name given."}

    cache_key = f"weather:{city.lower()}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",  # Celsius, not Fahrenheit or Kelvin
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        return {"error": f"Weather service timed out while looking up '{city}'. Try again."}
    except requests.exceptions.ConnectionError:
        return {"error": "Couldn't reach the weather service. Check your internet connection."}
    except requests.exceptions.RequestException as exc:
        return {"error": f"Weather request failed: {exc}"}

    if response.status_code == 404:
        return {"error": f"'{city}' doesn't look like a real place. Check the spelling?"}
    if response.status_code != 200:
        return {"error": f"Could not fetch weather for '{city}'. Status: {response.status_code}"}

    try:
        data = response.json()
        result = {
            "city": data["name"],
            "temperature_c": data["main"]["temp"],
            "feels_like_c": data["main"]["feels_like"],
            "condition": data["weather"][0]["description"],
            "humidity_pct": data["main"]["humidity"],
            "wind_speed_mps": data["wind"]["speed"],
        }
    except (ValueError, KeyError, IndexError, TypeError):
        # ValueError = bad JSON, the rest = missing/unexpected fields
        return {"error": f"Got an unexpected response for '{city}'. Try again in a moment."}

    _set_cached(cache_key, result)
    return result


def get_forecast(city: str, hours_ahead: int = 24) -> list:
    """Fetch upcoming forecast in 3-hour steps for the next `hours_ahead` hours.

    Always returns a list. On any failure it returns [] — callers should
    treat an empty list as "no forecast available" rather than an error,
    since the current-weather call already surfaces the real error message.
    """
    city = (city or "").strip()
    if not city:
        return []

    cache_key = f"forecast:{city.lower()}:{hours_ahead}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException:
        return []

    if response.status_code != 200:
        return []

    try:
        data = response.json()
        num_slots = max(1, hours_ahead // 3)  # each slot = 3 hours

        slots = []
        for entry in data["list"][:num_slots]:
            slots.append({
                "time": entry["dt_txt"],  # e.g. "2026-09-07 15:00:00"
                "temperature_c": entry["main"]["temp"],
                "condition": entry["weather"][0]["description"],
                "rain_chance_pct": round(entry.get("pop", 0) * 100),
                "wind_speed_mps": entry["wind"]["speed"],
            })
    except (ValueError, KeyError, IndexError, TypeError):
        return []

    _set_cached(cache_key, slots)
    return slots


if __name__ == "__main__":
    # Quick manual test — change the city and run this file directly
    test_city = "Delhi"
    result = get_weather(test_city)
    print(result)
    print("\nForecast:")
    for slot in get_forecast(test_city):
        print(slot)

    # Try a bad city too, to see the error handling in action
    print("\nBad city test:")
    print(get_weather("asdkfjhaskdjfh"))
