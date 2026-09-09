"""
WeatherGPT prototype — SIH26068
A conversational weather assistant with live data, alerts, and voice input.

Run: streamlit run app.py
(NOT python3 app.py — Streamlit needs its own command)
"""

import streamlit as st
from llm import ask_weathergpt, transcribe_audio, extract_city_llm
from alerts import check_alerts
from get_weather import get_weather

st.set_page_config(page_title="WeatherGPT", page_icon="⛅", layout="wide")

# ------------------------------------------------------------------
# Styling — dark weather-themed palette, rounded cards, cleaner chat
# ------------------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0B2A4A 0%, #071B30 100%);
    }
    section[data-testid="stSidebar"] {
        background-color: #0B2A4A;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    div[data-testid="stMetric"] {
        background-color: rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 14px 16px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    div[data-testid="stMetricLabel"] { color: #AFC9DE !important; }
    div[data-testid="stChatMessage"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 14px;
        padding: 4px 8px;
    }
    h1, h2, h3, p, label, span { color: #FFFFFF; }
    .subtitle { color: #AFC9DE; font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)


# A small list of major Indian cities for free-text matching.
# Add more cities here anytime — no code logic needs to change.
KNOWN_CITIES = [
    "Delhi", "Mumbai", "Bengaluru", "Bangalore", "Chennai", "Kolkata",
    "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh",
    "Bhopal", "Patna", "Guwahati", "Kochi", "Surat", "Nagpur",
]

# Rough emoji mapping so the weather card feels alive, not just numbers
CONDITION_EMOJI = {
    "clear": "☀️", "sun": "☀️", "cloud": "⛅", "overcast": "☁️",
    "rain": "🌧️", "drizzle": "🌦️", "thunderstorm": "⛈️",
    "snow": "❄️", "mist": "🌫️", "haze": "🌫️", "fog": "🌫️", "smoke": "🌫️",
}


def get_emoji(condition: str) -> str:
    condition = condition.lower()
    for key, emoji in CONDITION_EMOJI.items():
        if key in condition:
            return emoji
    return "🌡️"


def extract_city(question: str, fallback_city: str) -> str:
    """First try a fast keyword match against major known cities.
    If none matches, ask the LLM to extract any other city/town mentioned
    (e.g. Meerut, or anywhere not in the fixed list). Falls back to the
    sidebar-selected city only if no location is mentioned at all."""
    question_lower = question.lower()
    for city in KNOWN_CITIES:
        if city.lower() in question_lower:
            return "Bengaluru" if city == "Bangalore" else city

    extracted = extract_city_llm(question)
    if extracted and extracted.upper() != "NONE":
        return extracted

    return fallback_city


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⛅ WeatherGPT")
    st.caption("SIH26068 · Ministry of Earth Sciences")
    st.markdown("---")

    fallback_city = st.selectbox(
        "📍 Fallback location",
        ["Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata"],
    )
    st.caption("Used only if your question doesn't mention a city.")

    st.markdown("---")
    st.markdown("**🎙️ Ask by voice**")
    audio_value = st.audio_input("Record your question", label_visibility="collapsed")

    st.markdown("---")
    st.caption("🟢 Live data via OpenWeatherMap")
    st.caption("🤖 Answers grounded via Gemini")

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.markdown("# ⛅ WeatherGPT")
st.markdown(
    '<p class="subtitle">Conversational AI for weather forecasting, alerts & climate information</p>',
    unsafe_allow_html=True,
)
st.write("")

# ------------------------------------------------------------------
# Live snapshot card for the current fallback city
# ------------------------------------------------------------------
snapshot = get_weather(fallback_city)
if "error" not in snapshot:
    emoji = get_emoji(snapshot["condition"])
    st.markdown(f"#### {emoji} {snapshot['city']} — right now")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperature", f"{snapshot['temperature_c']}°C")
    col2.metric("Feels like", f"{snapshot['feels_like_c']}°C")
    col3.metric("Humidity", f"{snapshot['humidity_pct']}%")
    col4.metric("Wind", f"{snapshot['wind_speed_mps']} m/s")
    st.caption(snapshot["condition"].capitalize())

# Show any active alerts for the currently selected fallback city
for alert in check_alerts(fallback_city):
    if alert["level"] == "error":
        st.error(alert["message"])
    else:
        st.warning(alert["message"])

st.markdown("---")

# ------------------------------------------------------------------
# Chat
# ------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "⛅"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

transcribed_question = None
if audio_value is not None:
    audio_bytes = audio_value.read()
    audio_hash = hash(audio_bytes)
    # Only transcribe once per new recording, not on every rerun
    if st.session_state.get("last_audio_hash") != audio_hash:
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("Transcribing your question..."):
            transcribed_question = transcribe_audio(audio_bytes)

typed_question = st.chat_input("Ask about rain, temperature, wind, or safety — in your own words")
user_question = typed_question or transcribed_question

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user", avatar="🧑"):
        st.write(user_question)

    city = extract_city(user_question, fallback_city)

    if city != fallback_city:
        for alert in check_alerts(city):
            level = alert["level"]
            (st.error if level == "error" else st.warning)(alert["message"])

    with st.chat_message("assistant", avatar="⛅"):
        with st.spinner(f"Checking the forecast for {city}..."):
            answer = ask_weathergpt(city, user_question)
        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})