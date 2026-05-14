# 🌤️ Raspberry Pi Zero WH Weather Station

A beautiful, professional dark-mode weather dashboard that runs automatically on a Raspberry Pi Zero WH.

## Features

- **Auto location detection** (using IP geolocation on first run)
- **Real-time weather updates** every 30 seconds
- **Beautiful dark mode UI** – looks like a commercial weather station
- **No API key required** – Uses free Open-Meteo API
- **Auto-starts on boot** via systemd service
- **Accessible from any device** on your network (phone, tablet, laptop, etc.)

## Quick Setup on Raspberry Pi

```bash
cd ~/weather-station
chmod +x setup.sh
./setup.sh
