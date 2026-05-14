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
Access the Dashboard
After setup, open a web browser and go to:
http://YOUR_PI_IP:5000
Find your Pi's IP address with:
Bashhostname -I
Service Management
Bash# Check status
sudo systemctl status weather-station

# Restart
sudo systemctl restart weather-station

# Stop
sudo systemctl stop weather-station

# View live logs
sudo journalctl -u weather-station -f
Reset Location
If you move the Pi or want to change location:
Bashrm ~/.weather_station_config.json
sudo systemctl restart weather-station
Project Structure
textweather-station/
├── weatherapp.py
├── setup.sh
├── README.md
└── templates/
    └── dashboard.html
