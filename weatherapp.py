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
# INCREASED: 30 seconds hits Open-Meteo's limit too fast. 300s (5 mins) is optimal.
UPDATE_INTERVAL = 300 

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
IP_LOCATION_URL = "https://ipapi.co/json/"

weather_data = {}
air_quality_data = {}
location_data = {}
last_update = None

# Comprehensive code mapper to eliminate "Unknown" text bugs
WEATHER_CODE_MAP = {
    0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing Rime Fog",
    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    71: "Slight Snow", 73: "Moderate Snow", 75: "Heavy Snow",
    77: "Snow Grains", 80: "Slight Rain Showers", 81: "Moderate Rain Showers",
    82: "Violent Rain Showers", 85: "Slight Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm with Slight Hail", 99: "Thunderstorm with Heavy Hail"
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
        r = requests.get(IP_LOCATION_URL, timeout=5)
        data = r.json()
        lat = data.get("latitude")
        lon = data.get("longitude")
        # Extract dynamic location metadata string cleanly
        city = data.get("city", "Bristow")
        region = data.get("region_code", "VA")
        if lat and lon:
            return {"latitude": lat, "longitude": lon, "location_name": f"{city}, {region}"}
    except: pass
    return {"latitude": 38.75, "longitude": -77.55, "location_name": "Bristow, VA"}

def fetch_weather(lat, lon):
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            # ADDED: hourlyuv_index_clear_sky for advanced exposure tracking
            # ADDED: uv_index for real-time safety info
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,pressure_msl,is_day,uv_index",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code", # ADDED: daily weather_code for forecast emojis
            "hourly": "uv_index",
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
            "current": "us_aqi,pm2_5,pm10" # ADDED: Granular particle tracking
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except: return None

def update_weather_loop():
    global weather_data, air_quality_data, location_data, last_update
    
    while True:
        # Prevent crash if IP lookups error out temporarily
        try:
            if not location_data:
                location_data = load_config() or get_location_from_ip()
                
            data = fetch_weather(location_data["latitude"], location_data["longitude"])
            aq = fetch_air_quality(location_data["latitude"], location_data["longitude"])
            
            if data:
                weather_data = data
            if aq:
                air_quality_data = aq
                
            last_update = datetime.now().isoformat()
        except Exception as e:
            print(f"Loop execution warning: {e}")
            
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
    
    # Resolved: Map fallback strings correctly using comprehensive dict
    condition = WEATHER_CODE_MAP.get(code, "Clear Sky")

    # Generate daily forecasts with matching conditions/weather codes
    daily = weather_data.get("daily", {})
    daily_forecast = []
    if daily.get("time"):
        for i in range(min(7, len(daily["time"]))):
            day_code = daily.get("weather_code", [0]*7)[i]
            daily_forecast.append({
                "day": datetime.fromisoformat(daily["time"][i]).strftime("%a"),
                "max": round(daily["temperature_2m_max"][i]),
                "min": round(daily["temperature_2m_min"][i]),
                "code": day_code,
                "condition": WEATHER_CODE_MAP.get(day_code, "Clear Sky")
            })

    # Advanced Metrics Configuration
    aq_curr = air_quality_data.get("current", {}) if air_quality_data else {}
    aqi = aq_curr.get("us_aqi")
    
    # Calculate textual description tags for AQI 
    aqi_desc = "Good"
    if aqi and aqi > 50: aqi_desc = "Moderate"
    if aqi and aqi > 100: aqi_desc = "Unhealthy for Sensitive Groups"
    if aqi and aqi > 150: aqi_desc = "Unhealthy"

    return jsonify({
        "location": location_data.get("location_name", "Bristow, VA"),
        "temperature": round(current.get("temperature_2m", 0)),
        "feels_like": round(current.get("apparent_temperature", 0)),
        "humidity": current.get("relative_humidity_2m", "--"),
        "wind_speed": round(current.get("wind_speed_10m", 0), 1),
        "pressure": round(current.get("pressure_msl", 0)),
        "uv_index": current.get("uv_index", 0),
        "aqi": round(aqi) if aqi is not None else None,
        "aqi_description": aqi_desc,
        "pm2_5": aq_curr.get("pm2_5", 0),
        "pm10": aq_curr.get("pm10", 0),
        "condition": condition,
        "is_day": is_day,
        "daily": daily_forecast,
        "last_update": last_update
    })

if __name__ == '__main__':
    # Initialize structural memory parameters systematically before threads fork
    location_data = load_config() or get_location_from_ip()
    weather_data = fetch_weather(location_data["latitude"], location_data["longitude"])
    air_quality_data = fetch_air_quality(location_data["latitude"], location_data["longitude"])
    last_update = datetime.now().isoformat()

    threading.Thread(target=update_weather_loop, daemon=True).start()
    print("🌤️ Technical Weather Station backend started successfully")
    app.run(host='0.0.0.0', port=5000, debug=False)
