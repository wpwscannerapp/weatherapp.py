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

DEFAULT_LOCATION = {
    "latitude": 38.75,
    "longitude": -77.55,
    "location_name": "Bristow, VA",
}

def save_config(location):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(location, f)
    except Exception:
        pass

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return None

def get_location_from_ip():
    try:
        response = requests.get(IP_LOCATION_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        lat = data.get("latitude")
        lon = data.get("longitude")
        city = data.get("city", "Bristow")
        region = data.get("region_code", "VA")
        if lat is not None and lon is not None:
            return {
                "latitude": float(lat),
                "longitude": float(lon),
                "location_name": f"{city}, {region}",
            }
    except Exception:
        pass
    return DEFAULT_LOCATION.copy()

def resolve_location():
    saved = load_config()
    if saved:
        return saved

    location = get_location_from_ip()
    save_config(location)
    return location

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
                "current": "us_aqi,pm2_5,pm10"
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

def condition_to_emoji(condition_text, is_day=True):
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
    if "clear" in text:
        return "☀️" if is_day else "🌙"
    return "☀️" if is_day else "🌙"

def aqi_summary(aqi):
    if aqi is None:
        return "Unknown", "na"
    if aqi <= 50:
        return "Good", "good"
    if aqi <= 100:
        return "Moderate", "moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups", "warn"
    if aqi <= 200:
        return "Unhealthy", "warn"
    return "Very Unhealthy", "danger"

def build_dashboard():
    st.set_page_config(page_title="Weather Station", page_icon="🌤️", layout="wide")

    st.markdown("""
    <style>
        :root {
            --bg: #02050f;
            --bg-2: #071521;
            --panel: #0a1524;
            --panel-2: #0f1d2e;
            --line: #1d3b4a;
            --cyan: #00f4d0;
            --cyan-soft: #7df9d6;
            --text: #e5f5ff;
            --muted: #88a9b8;
            --amber: #ffc857;
            --good: #7ef9a2;
            --warn: #ffd166;
            --bad: #ff6b6b;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top, #0d1d2d, #02050f 45%);
            color: var(--text);
        }
        .block-container {
            max-width: 1280px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        .shell {
            background: linear-gradient(180deg, rgba(16,27,35,0.96), rgba(8,12,20,0.96));
            border: 1px solid var(--line);
            border-radius: 16px;
            box-shadow:

