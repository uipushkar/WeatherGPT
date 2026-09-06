"""
Hour 1 — WeatherGPT prototype
Fetches real weather data for a city from OpenWeatherMap.
Run: python get_weather.py
"""

import requests

# 1. Paste your OpenWeatherMap API key here
API_KEY = "df10d652e9a12909014f4a8d21d1a7e4"


def get_weather(city: str) -> dict:
    """Fetch current weather + forecast text for a given city."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",  # Celsius, not Fahrenheit or Kelvin
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return {"error": f"Could not fetch weather for '{city}'. Status: {response.status_code}"}

    data = response.json()

    return {
        "city": data["name"],
        "temperature_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "condition": data["weather"][0]["description"],
        "humidity_pct": data["main"]["humidity"],
        "wind_speed_mps": data["wind"]["speed"],
    }


def get_weather_mock(city: str) -> dict:
    """Fake data — use this temporarily while your API key is still activating."""
    return {
        "city": city,
        "temperature_c": 31.5,
        "feels_like_c": 34.0,
        "condition": "light rain",
        "humidity_pct": 68,
        "wind_speed_mps": 4.2,
    }


if __name__ == "__main__":
    test_city = "London"

    # Switch this to get_weather(test_city) once your API key is active
    result = get_weather_mock(test_city)
    print(result)
