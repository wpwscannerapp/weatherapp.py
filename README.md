# 🌤️ Weather Station

A dark, industrial-style weather dashboard built with Streamlit and the free Open-Meteo weather and air-quality APIs. No API key is required.

## Deploy on Streamlit Community Cloud

1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with your GitHub account and authorize access to this repository.
2. Click **Create app** (or use the [deploy page](https://share.streamlit.io/deploy)).
3. Select repository `wpwscannerapp/weatherapp.py`, branch `main`, and main file path `streamlit_app.py`.
4. Click **Deploy**. Streamlit installs the dependencies from `requirements.txt`.

The app entry point is `streamlit_app.py`; it loads the dashboard in `weatherapp.py`.

## Features

- Current conditions, feels-like temperature, humidity, wind, pressure, UV, and air quality
- Seven-day forecast
- Dark station-console interface and live clock
- Manual latitude/longitude settings
- Approximate IP-based location fallback and Bristow, VA fallback
- Cached API responses (up to five minutes) and a manual refresh button
- Weather condition notices for thunderstorms and some heavy precipitation (not official alerts)

> **Location note:** IP geolocation on a hosted service may identify the server rather than you. For an accurate forecast, enable **Set location manually** in the sidebar and enter your coordinates.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Files

- `streamlit_app.py` — Streamlit Cloud entry point
- `weatherapp.py` — dashboard and weather API implementation
- `requirements.txt` — Python dependencies

The old Flask template and Raspberry Pi setup scripts are not used by the Streamlit Cloud deployment.
