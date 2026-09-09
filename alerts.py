"""
Hour 6 — WeatherGPT prototype
Simple rule-based alerts: checks real current + forecast data against
fixed thresholds and returns any warnings that apply.

These thresholds are illustrative for a prototype — a production system
would tune them against IMD's actual warning criteria (e.g. cyclone
categories, heatwave definitions per region).

Hour 8 update: defensive checks so a missing/odd field in the weather
data can't throw a KeyError and take down the sidebar.
"""

from get_weather import get_weather, get_forecast

# Thresholds — adjust these freely, they're intentionally simple for a demo
WIND_ALERT_MPS = 10.8       # roughly IMD's "strong wind" threshold
HEAVY_RAIN_CHANCE_PCT = 70
HEATWAVE_TEMP_C = 40


def check_alerts(city: str) -> list:
    """Return a list of alert dicts: {level, message}.
    level is 'warning' or 'error' (error = more severe).

    Always returns a list — even if weather data is missing, malformed,
    or the city lookup failed — so the UI never crashes on this call.
    """
    alerts = []
    current = get_weather(city)

    if "error" in current:
        return alerts  # no data, no alerts — fail quietly

    try:
        # Current conditions checks
        if current["wind_speed_mps"] >= WIND_ALERT_MPS:
            alerts.append({
                "level": "error",
                "message": f"⚠️ Strong winds in {current['city']} — "
                           f"{current['wind_speed_mps']} m/s right now.",
            })

        if current["temperature_c"] >= HEATWAVE_TEMP_C:
            alerts.append({
                "level": "error",
                "message": f"🌡️ Heatwave conditions in {current['city']} — "
                           f"{current['temperature_c']}°C right now.",
            })
    except (KeyError, TypeError):
        # Shouldn't happen given get_weather's contract, but don't let a
        # missing field kill the sidebar during a live demo.
        pass

    # Forecast checks — look ahead for heavy rain in the next 24h
    forecast = get_forecast(city, hours_ahead=24)
    for slot in forecast:
        try:
            if slot["rain_chance_pct"] >= HEAVY_RAIN_CHANCE_PCT:
                alerts.append({
                    "level": "warning",
                    "message": f"🌧️ Heavy rain likely in {current['city']} around "
                               f"{slot['time']} — {slot['rain_chance_pct']}% chance.",
                })
                break  # one forecast alert is enough for the demo
        except (KeyError, TypeError):
            continue

    return alerts


if __name__ == "__main__":
    # Quick manual test
    test_city = "Delhi"
    for alert in check_alerts(test_city):
        print(alert)

    # Bad city — should just print nothing, not crash
    print("\nBad city test (should be silent):")
    for alert in check_alerts("asdkfjhaskdjfh"):
        print(alert)