#!/usr/bin/env python3
"""
🌤️ Professional Weather Station Dashboard for Raspberry Pi Zero WH
Dark mode, auto location detection, free Open-Meteo API
"""

from flask import Flask, render_template, jsonify
import requests
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Configuration
CONFIG_FILE = os.path.expanduser("~/.weather_station_config.json")
UPDATE_INTERVAL = 30  # seconds

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
IP_LOCATION_URL = "https://ipapi.co/json/"

# Global data
weather_data = {}
location_data = {}
last_update = None

# Weather codes
WEATHER_CODES = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Fog", "🌫️"), 48: ("Fog", "🌫️"),
    51: ("Light drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Slight snow", "🌨️"), 73: ("Snow", "🌨️"), 75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌦️"), 81: ("Rain showers", "🌧️"), 82: ("Heavy showers", "🌧️"),
    85: ("Snow showers", "🌨️"), 86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm", "⛈️"), 99: ("Thunderstorm", "⛈️"),
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return None

def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

def get_location_from_ip():
    try:
        print("🔍 Auto-detecting location...")
        r = requests.get(IP_LOCATION_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat and lon:
            name = f"{data.get('city', 'Unknown')}, {data.get('country_name', '')}"
            print(f"✅ Location detected: {name}")
            return {"latitude": lat, "longitude": lon, "location_name": name}
    except Exception as e:
        print(f"Location detection failed: {e}")
    return None

def fetch_weather(lat, lon):
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature",
            "timezone": "auto"
        }
        r = requests.get(WEATHER_API_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        return None

def update_weather_loop():
    global weather_data, location_data, last_update
    location_data = load_config() or get_location_from_ip()
    if location_data:
        save_config(location_data)

    while True:
        if location_data:
            data = fetch_weather(location_data["latitude"], location_data["longitude"])
            if data and "current" in data:
                weather_data = data
                last_update = datetime.now().isoformat()
        time.sleep(UPDATE_INTERVAL)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/weather')
def get_weather():
    if not weather_data or not location_data:
        return jsonify({"error": "Loading weather data..."}), 503

    current = weather_data.get("current", {})
    code = current.get("weather_code", 0)
    condition, emoji = WEATHER_CODES.get(code, ("Unknown", "🌡️"))

    return jsonify({
        "location": location_data.get("location_name"),
        "temperature": round(current.get("temperature_2m", 0), 1),
        "feels_like": round(current.get("apparent_temperature", 0), 1),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": round(current.get("wind_speed_10m", 0), 1),
        "condition": condition,
        "emoji": emoji,
        "last_update": last_update
    })

if __name__ == '__main__':
    threading.Thread(target=update_weather_loop, daemon=True).start()
    print("🌤️ Weather Station running at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
