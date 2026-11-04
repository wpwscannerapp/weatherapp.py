from datetime import datetime
import re

import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
IP_LOCATION_URL = "https://ipapi.co/json/"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
ZIP_LOOKUP_URL = "https://api.zippopotam.us/us/"
DEFAULT_LOCATION = {"latitude": 38.75, "longitude": -77.55, "location_name": "Bristow, VA"}
WEATHER_CODE_MAP = {
    0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing Rime Fog", 51: "Light Drizzle",
    53: "Moderate Drizzle", 55: "Dense Drizzle", 61: "Slight Rain",
    63: "Moderate Rain", 65: "Heavy Rain", 71: "Slight Snow",
    73: "Moderate Snow", 75: "Heavy Snow", 77: "Snow Grains",
    80: "Slight Rain Showers", 81: "Moderate Rain Showers",
    82: "Violent Rain Showers", 85: "Slight Snow Showers",
    86: "Heavy Snow Showers", 95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail", 99: "Thunderstorm with Heavy Hail",
}

st.set_page_config(page_title="Weather Station", page_icon="🌤️", layout="wide")


@st.cache_data(ttl=3600, show_spinner=False)
def locate_by_ip():
    """Best-effort IP location; on hosted services it may identify the server."""
    try:
        response = requests.get(IP_LOCATION_URL, timeout=6)
        response.raise_for_status()
        data = response.json()
        lat, lon = data.get("latitude"), data.get("longitude")
        if lat is not None and lon is not None:
            city = data.get("city") or "Nearby"
            region = data.get("region_code") or data.get("region") or ""
            return {
                "latitude": float(lat),
                "longitude": float(lon),
                "location_name": f"{city}, {region}".strip(", "),
            }
    except (requests.RequestException, ValueError, TypeError):
        pass
    return DEFAULT_LOCATION.copy()


@st.cache_data(ttl=3600, show_spinner=False)
def search_places(query):
    """Resolve a US ZIP code or search worldwide city names."""
    query = query.strip()
    if re.fullmatch(r"\d{5}", query):
        try:
            response = requests.get(f"{ZIP_LOOKUP_URL}{query}", timeout=8)
            if response.ok:
                data = response.json()
                place = data.get("places", [{}])[0]
                return [{
                    "latitude": float(place["latitude"]),
                    "longitude": float(place["longitude"]),
                    "location_name": f"{place.get('place name', query)}, {place.get('state abbreviation', '')} {query}".strip(),
                }]
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
            pass

    try:
        response = requests.get(
            GEOCODING_URL,
            params={"name": query, "count": 8, "language": "en", "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return [
            {
                "latitude": float(item["latitude"]),
                "longitude": float(item["longitude"]),
                "location_name": ", ".join(
                    part for part in (item.get("name"), item.get("admin1"), item.get("country")) if part
                ),
            }
            for item in results
        ]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_weather(latitude, longitude):
    response = requests.get(
        WEATHER_API_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,pressure_msl,is_day,uv_index",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code,sunrise,sunset",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
            "forecast_days": 7,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_air_quality(latitude, longitude):
    response = requests.get(
        AIR_QUALITY_URL,
        params={"latitude": latitude, "longitude": longitude, "current": "us_aqi,pm2_5,pm10"},
        timeout=12,
    )
    response.raise_for_status()
    return response.json()


def condition_emoji(condition, is_day=True):
    text = (condition or "").lower()
    if "thunderstorm" in text:
        return "⛈️"
    if "rain" in text or "drizzle" in text:
        return "🌧️"
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


def aqi_description(aqi):
    if aqi is None:
        return "Unavailable"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


def show_metric(label, value, accent=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value" style="{accent}">{value}</div></div>',
        unsafe_allow_html=True,
    )


def set_kiosk(enabled):
    if enabled:
        st.query_params["kiosk"] = "1"
    else:
        st.query_params.clear()
    st.rerun()


is_kiosk = st.query_params.get("kiosk") == "1"

st.markdown("""
<style>
:root { --bg:#030811; --line:#1d3b4a; --cyan:#00f4d0; --text:#e5f5ff; --muted:#88a9b8; }
[data-testid="stAppViewContainer"] { background:radial-gradient(circle at top,#102131,#030811 48%); color:var(--text); }
.block-container { max-width:1280px; padding-top:1.2rem; padding-bottom:2rem; }
.station { background:linear-gradient(180deg,rgba(16,27,35,.97),rgba(8,12,20,.97)); border:1px solid var(--line); border-radius:16px; padding:1.2rem 1.4rem; box-shadow:0 0 0 1px rgba(0,244,208,.12),0 0 32px rgba(0,244,208,.08); }
.brand { color:var(--cyan); font-size:clamp(1.7rem,4vw,2.7rem); font-weight:800; letter-spacing:.14rem; }
.kicker { color:var(--muted); font:.75rem monospace; letter-spacing:.18rem; text-transform:uppercase; }
.hero { text-align:center; padding:1.3rem .5rem; border-bottom:1px solid rgba(125,249,214,.15); margin-bottom:1.1rem; }
.hero-icon { font-size:6.5rem; line-height:1.1; filter:drop-shadow(0 0 14px rgba(0,244,208,.15)); }
.hero-temp { font:800 clamp(3rem,8vw,4.5rem) monospace; color:var(--text); }
.hero-condition { color:#7df9d6; font-size:1.05rem; letter-spacing:.1rem; text-transform:uppercase; }
.metric-card { background:rgba(11,24,37,.85); border:1px solid rgba(125,249,214,.2); border-radius:12px; padding:1rem .5rem; text-align:center; min-height:110px; }
.metric-label { color:var(--muted); text-transform:uppercase; letter-spacing:.08rem; font-size:.66rem; min-height:2rem; }
.metric-value { color:var(--text); font:700 clamp(1.1rem,2vw,1.7rem) monospace; overflow-wrap:anywhere; }
.section-title { color:#7df9d6; text-transform:uppercase; text-align:center; letter-spacing:.18rem; margin:1.5rem 0 .8rem; }
.forecast { background:rgba(8,18,26,.9); border:1px solid rgba(125,249,214,.2); border-radius:12px; padding:.8rem .35rem; text-align:center; min-height:130px; }
.forecast-day { color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.1rem; }
.forecast-icon { font-size:1.8rem; margin:.4rem 0; }
.status { color:var(--muted); text-align:center; font:.75rem monospace; margin-top:1.2rem; }
.notice { color:#ffe3a3; background:rgba(125,66,0,.24); border:1px solid #9a6b27; padding:.75rem 1rem; border-radius:9px; margin:.8rem 0; }
[data-testid="stSidebar"] { background:#08111c; }
body:has([data-testid="stAppViewContainer"]) { margin:0; }
.kiosk-mode .block-container { max-width:1600px; padding-top:.35rem; }
@media (max-width:760px) { .block-container {padding-left:.6rem;padding-right:.6rem;} .station {padding:.8rem;} .hero-icon {font-size:4.8rem;} }
</style>
""", unsafe_allow_html=True)

if is_kiosk:
    st.markdown("<style>[data-testid='stHeader'],[data-testid='stSidebar'],footer{display:none!important}.block-container{max-width:1600px!important;padding-top:.4rem!important}</style>", unsafe_allow_html=True)
    if st.button("Exit kiosk mode"):
        set_kiosk(False)
else:
    with st.sidebar:
        st.markdown("## ⚙️ Station Controls")
        mode = st.radio("Location source", ["City / ZIP lookup", "Automatic IP location", "Manual coordinates"], index=0)
        location = None

        if mode == "City / ZIP lookup":
            with st.form("place_search"):
                place_query = st.text_input("City or US ZIP code", value=st.session_state.get("place_query", "Bristow, VA"), placeholder="e.g. Boston, MA or 02108")
                search_submitted = st.form_submit_button("Find location", use_container_width=True)
            if search_submitted:
                st.session_state.place_query = place_query
                with st.spinner("Finding location…"):
                    st.session_state.place_results = search_places(place_query)
                st.session_state.place_selected = None
            results = st.session_state.get("place_results", [])
            if results:
                labels = [result["location_name"] for result in results]
                selected_label = st.selectbox("Choose a match", labels)
                if st.button("Use this location", use_container_width=True):
                    st.session_state.active_location = results[labels.index(selected_label)]
                location = st.session_state.get("active_location")
            elif search_submitted:
                st.error("No match found. Try a nearby city, a full city/state, or a valid 5-digit US ZIP code.")
            if location is None:
                location = st.session_state.get("active_location", DEFAULT_LOCATION.copy())
                st.caption("Default location is Bristow, VA. Search for a city or US ZIP to change it.")
        elif mode == "Automatic IP location":
            location = locate_by_ip()
            st.caption(f"Approximate IP location: {location['location_name']}. Hosted services may report their server's location, not yours.")
        else:
            latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=float(DEFAULT_LOCATION["latitude"]), step=0.01, format="%.4f")
            longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=float(DEFAULT_LOCATION["longitude"]), step=0.01, format="%.4f")
            location_name = st.text_input("Location label", value="Custom Location")
            location = {"latitude": latitude, "longitude": longitude, "location_name": location_name or "Custom Location"}

        st.divider()
        if st.button("↻ Refresh weather now", use_container_width=True):
            fetch_weather.clear()
            fetch_air_quality.clear()
            st.rerun()
        if st.button("⛶ Enter kiosk mode", use_container_width=True):
            set_kiosk(True)
        st.caption("Weather data refreshes every 5 minutes. Kiosk mode hides Streamlit controls; press F11 or use your browser's kiosk launch option for true fullscreen.")

if is_kiosk:
    location = st.session_state.get("active_location", DEFAULT_LOCATION.copy())

# Refresh Streamlit's page periodically. Cached API requests still respect their 5-minute TTL.
st_autorefresh(interval=300_000, limit=None, key="weather_auto_refresh")

try:
    with st.spinner("Connecting to weather station…"):
        weather = fetch_weather(float(location["latitude"]), float(location["longitude"]))
except (requests.RequestException, ValueError, KeyError) as exc:
    st.error(f"Could not retrieve weather data: {exc}")
    st.stop()

try:
    air_quality = fetch_air_quality(float(location["latitude"]), float(location["longitude"]))
except requests.RequestException:
    air_quality = None

current = weather.get("current", {})
daily = weather.get("daily", {})
weather_code = current.get("weather_code", 0)
condition = WEATHER_CODE_MAP.get(weather_code, "Unknown Conditions")
is_day = bool(current.get("is_day", 1))
aq_current = (air_quality or {}).get("current", {})
aq_index = aq_current.get("us_aqi")

if weather_code in (95, 96, 99, 65, 82):
    st.markdown(f'<div class="notice">⚠️ Current condition: <b>{condition}</b>. This is not an official severe-weather alert.</div>', unsafe_allow_html=True)

st.markdown('<div class="station">', unsafe_allow_html=True)
header, clock = st.columns([4, 1])
with header:
    st.markdown('<div class="kicker">Local forecast · Open-Meteo</div><div class="brand">🌤 WEATHER STATION</div>', unsafe_allow_html=True)
with clock:
    components.html("""<div id="weather-clock" style="text-align:right;color:#e5f5ff;font:bold 1.6rem monospace"></div><script>
function updateClock(){const d=new Date();document.getElementById('weather-clock').textContent=d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});}
updateClock();setInterval(updateClock,1000);
</script>""", height=38)

st.markdown(
    f'<div class="hero"><div class="hero-icon">{condition_emoji(condition, is_day)}</div>'
    f'<div class="hero-temp">{round(current.get("temperature_2m", 0))}°F</div>'
    f'<div class="hero-condition">{condition} &nbsp;•&nbsp; Feels like {round(current.get("apparent_temperature", 0))}°F</div></div>',
    unsafe_allow_html=True,
)

metric_columns = st.columns(6)
metrics = [
    ("Humidity", f"{current.get('relative_humidity_2m', '—')}%", ""),
    ("Wind", f"{current.get('wind_speed_10m', '—')} mph", ""),
    ("Pressure", f"{round(current.get('pressure_msl', 0))} hPa", ""),
    ("UV Index", str(current.get("uv_index", "—")), "color:#ffc857"),
    (f"AQI · {aqi_description(aq_index)}", str(round(aq_index)) if aq_index is not None else "—", ""),
    ("PM2.5", f"{aq_current.get('pm2_5', '—')} µg/m³", ""),
]
for column, (label, value, accent) in zip(metric_columns, metrics):
    with column:
        show_metric(label, value, accent)

sunrise = daily.get("sunrise", [])
sunset = daily.get("sunset", [])
if sunrise and sunset:
    st.caption(f"Sunrise {sunrise[0].split('T')[-1]} · Sunset {sunset[0].split('T')[-1]} (local time)")

st.markdown('<div class="section-title">7-Day Forecast</div>', unsafe_allow_html=True)
forecast_columns = st.columns(7)
times = daily.get("time", [])
maxima = daily.get("temperature_2m_max", [])
minima = daily.get("temperature_2m_min", [])
codes = daily.get("weather_code", [])
for index, column in enumerate(forecast_columns):
    if index >= min(len(times), len(maxima), len(minima)):
        continue
    day_condition = WEATHER_CODE_MAP.get(codes[index], "Unknown Conditions") if index < len(codes) else "Unknown Conditions"
    try:
        day_name = datetime.fromisoformat(times[index]).strftime("%a")
    except (TypeError, ValueError):
        day_name = str(times[index])
    with column:
        st.markdown(
            f'<div class="forecast"><div class="forecast-day">{day_name}</div>'
            f'<div class="forecast-icon">{condition_emoji(day_condition)}</div>'
            f'<div style="font-weight:700">{round(maxima[index])}°</div>'
            f'<div style="color:#88a9b8">{round(minima[index])}°</div></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    f'<div class="status">LOCATION: {location.get("location_name", "Weather Station")} &nbsp; // &nbsp; '
    f'UPDATED: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} &nbsp; // &nbsp; SOURCE: OPEN-METEO</div>',
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)
