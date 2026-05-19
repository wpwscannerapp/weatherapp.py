#!/usr/bin/env python3
"""
🌤️ Technical Weather Station - Day/Night Emojis + Professional UI
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
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
IP_LOCATION_URL = "https://ipapi.co/json/"

weather_data = {}
air_quality_data = {}
location_data = {}
last_update = None

# Enhanced weather codes with day/night support handled in frontend
WEATHER_CODES = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
    71: "🌨️", 73: "🌨️", 75: "❄️",
    95: "⛈️", 96: "⛈️", 99: "⛈️"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except: pass
    return None

def get_location_from_ip():
    try:
        r = requests.get(IP_LOCATION_URL, timeout=10)
        data = r.json()
        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat and lon:
            return {"latitude": lat, "longitude": lon, "location_name": "Bristow, VA"}
    except: pass
    return {"latitude": 38.75, "longitude": -77.55, "location_name": "Bristow, VA"}

def fetch_weather(lat, lon):
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,pressure_msl,is_day",
            "daily": "temperature_2m_max,temperature_2m_min",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
            "forecast_days": 7
        }
        r = requests.get(WEATHER_API_URL, params=params, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Weather Error: {e}")
        return None

def fetch_air_quality(lat, lon):
    try:
        r = requests.get(AIR_QUALITY_URL, params={
            "latitude": lat,
            "longitude": lon,
            "current": "us_aqi"
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except: return None

def update_weather_loop():
    global weather_data, air_quality_data, location_data, last_update
    location_data = load_config() or get_location_from_ip()

    while True:
        data = fetch_weather(location_data["latitude"], location_data["longitude"])
        aq = fetch_air_quality(location_data["latitude"], location_data["longitude"])
        
        if data:
            weather_data = data
        if aq:
            air_quality_data = aq
            
        last_update = datetime.now().isoformat()
        time.sleep(UPDATE_INTERVAL)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/weather')
def get_weather():
    if not weather_data:
        return jsonify({"status": "loading", "location": "Bristow, VA"})

    current = weather_data.get("current", {})
    code = current.get("weather_code", 0)
    is_day = current.get("is_day", 1)

    condition = {
        0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
        45: "Fog", 61: "Rain", 63: "Rain", 65: "Heavy Rain",
        71: "Snow", 95: "Thunderstorm"
    }.get(code, "Unknown")

    daily = weather_data.get("daily", {})
    daily_forecast = []
    if daily.get("time"):
        for i in range(min(7, len(daily["time"]))):
            daily_forecast.append({
                "day": datetime.fromisoformat(daily["time"][i]).strftime("%a"),
                "max": round(daily["temperature_2m_max"][i]),
                "min": round(daily["temperature_2m_min"][i])
            })

    aq = air_quality_data.get("current", {}) if air_quality_data else {}
    aqi = aq.get("us_aqi")

    return jsonify({
        "location": location_data.get("location_name", "Bristow, VA"),
        "temperature": round(current.get("temperature_2m", 0)),
        "feels_like": round(current.get("apparent_temperature", 0)),
        "humidity": current.get("relative_humidity_2m", "--"),
        "wind_speed": round(current.get("wind_speed_10m", 0), 1),
        "pressure": round(current.get("pressure_msl", 0)),
        "aqi": round(aqi) if aqi is not None else None,
        "condition": condition,
        "is_day": is_day,
        "daily": daily_forecast,
        "last_update": last_update
    })

if __name__ == '__main__':
    location_data = load_config() or get_location_from_ip()
    weather_data = fetch_weather(location_data["latitude"], location_data["longitude"])
    air_quality_data = fetch_air_quality(location_data["latitude"], location_data["longitude"])
    last_update = datetime.now().isoformat()

    threading.Thread(target=update_weather_loop, daemon=True).start()
    print("🌤️ Technical Weather Station started")
    app.run(host='0.0.0.0', port=5000, debug=False)
