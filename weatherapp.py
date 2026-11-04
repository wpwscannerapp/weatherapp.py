import json
import os
from datetime import datetime

import requests
import streamlit as st

CONFIG_FILE = os.path.expanduser("~/.weather_station_config.json")
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
IP_LOCATION_URL = "https://ipapi.co/json/"

WEATHER_CODE_MAP = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail",
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def get_location_from_ip():
    try:
        response = requests.get(IP_LOCATION_URL, timeout=5)
        data = response.json()
        lat = data.get("latitude")
        lon = data.get("longitude")
        city = data.get("city", "Bristow")
        region = data.get("region_code", "VA")
        if lat and lon:
            return {
                "latitude": lat,
                "longitude": lon,
                "location_name": f"{city}, {region}",
            }
    except Exception:
        pass

    return {
        "latitude": 38.75,
        "longitude": -77.55,
        "location_name": "Bristow, VA",
    }


@st.cache_data(ttl=300)
def fetch_weather(lat, lon):
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,pressure_msl,is_day,uv_index",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "hourly": "uv_index",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
            "forecast_days": 7,
        }
        response = requests.get(WEATHER_API_URL, params=params, timeout=12)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        st.warning(f"Weather fetch failed: {exc}")
        return None


@st.cache_data(ttl=300)
def fetch_air_quality(lat, lon):
    try:
        response = requests.get(
            AIR_QUALITY_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "us_aqi,pm2_5,pm10",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_location_and_weather():
    location = load_config() or get_location_from_ip()
    weather_data = fetch_weather(location["latitude"], location["longitude"])
    air_quality_data = fetch_air_quality(location["latitude"], location["longitude"])
    return location, weather_data, air_quality_data


def get_condition_emoji(condition_text, is_day):
    text = (condition_text or "").lower()
    if "thunderstorm" in text:
        return "⛈️"
    if "heavy rain" in text or "violent" in text:
        return "🌧️"
    if "rain" in text or "drizzle" in text:
        return "🌦️"
    if "snow" in text or "grains" in text:
        return "🌨️"
    if "fog" in text:
        return "🌫️"
    if "overcast" in text:
        return "☁️"
    if "partly cloudy" in text:
        return "⛅"
    if "mainly clear" in text:
        return "🌤️"
    return "☀️" if is_day else "🌙"


def build_dashboard():
    st.set_page_config(page_title="Weather Station", page_icon="🌤️", layout="wide")

    st.markdown(
        """
        <style>
        :root {
            --bg: #02050f;
            --panel: #0a0f1f;
            --panel-2: rgba(0, 30, 40, 0.6);
            --border: #00cc99;
            --text: #eaf6ff;
            --muted: #88aaaa;
            --accent: #00ffcc;
            --amber: #ffcc00;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: var(--bg);
            color: var(--text);
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        .station-box {
            background: var(--panel);
            border: 2px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem 1.5rem 2rem;
            box-shadow: 0 0 40px rgba(0, 255, 204, 0.2);
        }
        .title {
            font-size: 2.8rem;
            font-weight: 800;
            letter-spacing: 0.18rem;
            color: var(--accent);
            margin: 0;
        }
        .clock {
            font-size: 3rem;
            font-weight: 700;
            color: var(--text);
            text-align: right;
        }
        .metric-card {
            background: var(--panel-2);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem 0.8rem;
            text-align: center;
            min-height: 120px;
        }
        .metric-label {
            font-size: 0.7rem;
            color: var(--muted);
            letter-spacing: 0.12rem;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text);
        }
        .forecast-card {
            background: rgba(5, 15, 30, 0.8);
            border: 1px solid #334455;
            border-radius: 10px;
            padding: 0.9rem 0.5rem;
            text-align: center;
            min-height: 140px;
        }
        .forecast-day {
            font-size: 0.72rem;
            color: var(--muted);
            letter-spacing: 0.12rem;
            text-transform: uppercase;
        }
        .forecast-emoji {
            font-size: 2rem;
            margin: 0.4rem 0;
        }
        .status {
            color: var(--muted);
            font-size: 0.8rem;
            letter-spacing: 0.08rem;
            text-align: center;
            margin-top: 1.5rem;
        }
        @media (max-width: 768px) {
            .title { font-size: 2rem; }
            .clock { font-size: 2rem; text-align: left; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    location, weather_data, air_quality_data = get_location_and_weather()

    if not weather_data:
        st.error("Unable to load weather data right now. Check your internet connection and try again.")
        return

    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    code = current.get("weather_code", 0)
    is_day = current.get("is_day", 1)
    condition = WEATHER_CODE_MAP.get(code, "Clear Sky")

    daily_forecast = []
    if daily.get("time"):
        for i in range(min(7, len(daily["time"]))):
            day_code = daily.get("weather_code", [0] * 7)[i]
            daily_forecast.append(
                {
                    "day": datetime.fromisoformat(daily["time"][i]).strftime("%a"),
                    "max": round(daily["temperature_2m_max"][i]),
                    "min": round(daily["temperature_2m_min"][i]),
                    "condition": WEATHER_CODE_MAP.get(day_code, "Clear Sky"),
                }
            )

    aq_current = air_quality_data.get("current", {}) if air_quality_data else {}
    aqi = aq_current.get("us_aqi")
    if aqi is None:
        aqi_desc = "Unknown"
    elif aqi <= 50:
        aqi_desc = "Good"
    elif aqi <= 100:
        aqi_desc = "Moderate"
    elif aqi <= 150:
        aqi_desc = "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        aqi_desc = "Unhealthy"
    else:
        aqi_desc = "Very Unhealthy"

    current_time = datetime.now().strftime("%I:%M:%S %p")

    with st.container():
        st.markdown('<div class="station-box">', unsafe_allow_html=True)
        col_title, col_clock = st.columns([4, 1])
        with col_title:
            st.markdown('<div class="title">WEATHER STATION</div>', unsafe_allow_html=True)
        with col_clock:
            st.markdown(f'<div class="clock">{current_time}</div>', unsafe_allow_html=True)

        st.markdown(
            f"<div style='text-align:center; margin: 1.5rem 0 1rem;'><div style='font-size: 8rem; line-height: 1;'>{get_condition_emoji(condition, is_day)}</div><div style='font-size: 3.2rem; font-weight: 800; margin-top: 0.3rem;'>{round(current.get('temperature_2m', 0))}°F</div><div style='font-size: 1.4rem; color: #00ccaa; letter-spacing: 0.12rem; text-transform: uppercase; margin-top: 0.25rem;'>{condition} • FEELS {round(current.get('apparent_temperature', 0))}°F</div></div>",
            unsafe_allow_html=True,
        )

        metric_cols = st.columns(6)
        metric_values = [
            ("Humidity", f"{current.get('relative_humidity_2m', '--')}%"),
            ("Wind Speed", f"{round(current.get('wind_speed_10m', 0), 1)} mph"),
            ("Barometer", f"{round(current.get('pressure_msl', 0))} hPa"),
            ("UV Index", str(current.get("uv_index", 0))),
            (f"AQI ({aqi_desc})", str(round(aqi) if aqi is not None else "--")),
            ("PM2.5", f"{aq_current.get('pm2_5', 0)} µg"),
        ]

        for col, (label, value) in zip(metric_cols, metric_values):
            with col:
                st.markdown(
                    f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>",
                    unsafe_allow_html=True,
                )

        st.markdown('<h3 style="text-align:center; color:#00ccaa; letter-spacing:0.16rem; margin: 2rem 0 1rem;">7-DAY FORECAST</h3>', unsafe_allow_html=True)
        forecast_cols = st.columns(7)
        for col, day in zip(forecast_cols, daily_forecast):
            with col:
                st.markdown(
                    f"""
                    <div class="forecast-card">
                        <div class="forecast-day">{day['day']}</div>
                        <div class="forecast-emoji">{get_condition_emoji(day['condition'], True)}</div>
                        <div style="font-size:1.05rem; font-weight:700;">{day['max']}°</div>
                        <div style="font-size:0.8rem; color:#557788;">{day['min']}°</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown(
            f"<div class='status'>LOCATION: {location.get('location_name', 'Bristow, VA')} // LAST SYNC: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    build_dashboard()
