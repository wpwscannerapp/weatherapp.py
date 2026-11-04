# 🌤️ Weather Station

A dark, industrial-style weather dashboard built with Streamlit and the free Open-Meteo weather and air-quality APIs. No API key is required.

## Deploy on Streamlit Community Cloud

1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub and select **Create app**.
2. Choose repository `wpwscannerapp/weatherapp.py` and branch `main`.
3. Set the main file path to `streamlit_app.py`, then click **Deploy**.
4. Streamlit Cloud installs the packages from `requirements.txt` automatically.

## Location options

- **City / ZIP lookup** searches city names worldwide and resolves five-digit US ZIP codes. The initial location is Bristow, VA; search for your own place in the sidebar.
- **Automatic IP location** is approximate. On a hosted service, IP geolocation may locate the app server rather than the person viewing the app.
- **Manual coordinates** lets you enter latitude and longitude directly.

## Kiosk mode and clock

Use **Enter kiosk mode** in the sidebar to hide Streamlit navigation and controls. The dashboard clock updates every second in the browser, and weather data refreshes every five minutes. Browsers do not allow websites to force fullscreen without a user action; press **F11** or launch the browser with its kiosk/fullscreen option for a true full-screen display. Exit kiosk mode using the on-screen button.

## Features

- Current conditions, feels-like temperature, humidity, wind, pressure, UV, and air quality
- Seven-day forecast and sunrise/sunset
- Dark station-console interface, live clock, and scheduled refresh
- Manual refresh and cached API requests
- Weather condition notices for thunderstorms and certain heavy precipitation; these are not official severe-weather alerts

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```
