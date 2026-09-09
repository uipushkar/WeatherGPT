"""
Hour 2 — WeatherGPT prototype
Sends real weather data + the user's question to Gemini, so the LLM
explains the data instead of guessing numbers on its own.

Run: python llm.py
"""

import google.genai as genai
from google.genai import types
from get_weather import get_weather, get_forecast

# 1. Paste your Gemini API key here
GEMINI_API_KEY = "GEMINI_API_KEY"

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.6-flash"  # fast + free-tier friendly


def ask_weathergpt(city: str, question: str) -> str:
    """Fetch real current + forecast weather data for the city, then ask
    Gemini to answer the user's question using ONLY that data."""

    current = get_weather(city)
    forecast = get_forecast(city, hours_ahead=24)

    if "error" in current:
        return f"Sorry, I couldn't get weather data for {city}."

    forecast_lines = "\n".join(
        f"- {slot['time']}: {slot['temperature_c']}°C, {slot['condition']}, "
        f"{slot['rain_chance_pct']}% rain chance, wind {slot['wind_speed_mps']} m/s"
        for slot in forecast
    )

    prompt = f"""You are WeatherGPT, a helpful weather assistant.

Here is the REAL current weather data for {current['city']}:
- Temperature: {current['temperature_c']}°C (feels like {current['feels_like_c']}°C)
- Condition: {current['condition']}
- Humidity: {current['humidity_pct']}%
- Wind speed: {current['wind_speed_mps']} m/s

Here is the REAL forecast for the next 24 hours, in 3-hour steps:
{forecast_lines}

User's question: "{question}"

Answer the user's question naturally and helpfully, using ONLY the data above.
If the question asks about a specific time, pick the closest available forecast slot
and mention which time slot you're using. Do not invent any numbers not given here.
Keep the answer short (2-3 sentences)."""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text


def extract_city_llm(question: str) -> str:
    """Ask Gemini to pull out any city/town mentioned in the question,
    for cases outside a fixed known-cities list."""
    prompt = f"""Extract the name of the city or town mentioned in this weather question, if any.

Question: "{question}"

Respond with ONLY the location name (e.g. "Meerut"), with correct spelling and
no extra words. If no location is mentioned at all, respond with exactly: NONE"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text.strip()


def transcribe_audio(audio_bytes: bytes) -> str:
    """Send recorded audio straight to Gemini and get back the transcribed
    text — no separate speech-to-text service needed."""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            "Transcribe the spoken question in this audio exactly as spoken. "
            "Output ONLY the transcribed text, with no extra commentary or quotes.",
        ],
    )
    return response.text.strip()


if __name__ == "__main__":
    # Quick manual test
    answer = ask_weathergpt("Delhi", "Should I carry an umbrella today?")
    print(answer)
