#!/usr/bin/env python3
"""
🌤️ Advanced Weather Station - Technical Dashboard
Fahrenheit + More Data + Better Time Handling
"""

from flask import Flask, render_template, jsonify
import requests
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

CONFIG_FILE = os.path.expanduser("~/.weather_station_config.json")
UPDATE_INTERVAL = 30

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
IP_LOCATION_URL = "https://ipapi.co/json/"

weather_data = {}
location_data = {}
last_update = None

WEATHER_CODES = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Fog", "🌫️"), 48: ("Fog", "🌫️"),
    51: ("Light drizzle", "🌦️"), 61: ("Rain", "🌧️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Snow", "🌨️"), 73: ("Snow", "🌨️"), 75: ("Heavy snow", "❄️"),
    95: ("Thunderstorm", "⛈️"), 99: ("Thunderstorm", "⛈️"),
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return None

def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except: pass

def get_location_from_ip():
    try:
        r = requests.get(IP_LOCATION_URL, timeout=10)
        data = r.json()
        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat and lon:
            name = f"{data.get('city', 'Unknown')}, {data.get('region', '')} {data.get('country_code', '')}"
            return {"latitude": lat, "longitude": lon, "location_name": name}
    except: pass
    return None

def fetch_weather(lat, lon):
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,pressure_msl,dew_point_2m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
            "forecast_days": 7
        }
        r = requests.get(WEATHER_API_URL, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Fetch error: {e}")
        return None

def update_weather_loop():
    global weather_data, location_data, last_update
    location_data = load_config() or get_location_from_ip()
    if location_data:
        save_config(location_data)

    while True:
        if location_data:
            data = fetch_weather(location_data["latitude"], location_data["longitude"])
            if data:
                weather_data = data
                last_update = datetime.now().isoformat()
        time.sleep(UPDATE_INTERVAL)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/weather')
def get_weather():
    if not weather_data or not location_data:
        return jsonify({"error": "Loading..."}), 503

    current = weather_data.get("current", {})
    code = current.get("weather_code", 0)
    condition, emoji = WEATHER_CODES.get(code, ("Unknown", "🌡️"))

    daily = weather_data.get("daily", {})
    daily_forecast = []
    if daily and "time" in daily:
        for i in range(min(7, len(daily["time"]))):
            daily_forecast.append({
                "day": datetime.fromisoformat(daily["time"][i]).strftime("%a"),
                "max": round(daily["temperature_2m_max"][i]),
                "min": round(daily["temperature_2m_min"][i])
            })

    return jsonify({
        "location": location_data.get("location_name"),
        "temperature": round(current.get("temperature_2m", 0)),
        "feels_like": round(current.get("apparent_temperature", 0)),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": round(current.get("wind_speed_10m", 0), 1),
        "pressure": round(current.get("pressure_msl", 0)),
        "dew_point": round(current.get("dew_point_2m", 0), 1),
        "condition": condition,
        "emoji": emoji,
        "daily": daily_forecast,
        "last_update": last_update,
        "timezone": weather_data.get("timezone", "UTC")
    })

if __name__ == '__main__':
    threading.Thread(target=update_weather_loop, daemon=True).start()
    print("🌤️ Weather Station running")
    app.run(host='0.0.0.0', port=5000, debug=False)
