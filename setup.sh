#!/bin/bash

echo "🌤️ Weather Station Setup for Raspberry Pi Zero WH"
echo "=================================================="

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Install required packages
echo "📦 Installing dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment and install Python packages
cd /home/pi/weather-station
python3 -m venv venv
source venv/bin/activate
pip install --quiet flask requests

echo "✅ Dependencies installed successfully"

# Create systemd service for auto-start on boot
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/weather-station.service > /dev/null << EOF
[Unit]
Description=Weather Station Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/weather-station
Environment="PATH=/home/pi/weather-station/venv/bin"
ExecStart=/home/pi/weather-station/venv/bin/python3 /home/pi/weather-station/weatherapp.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable weather-station
sudo systemctl start weather-station

echo "✅ Setup completed successfully!"
echo ""
echo "🌐 Your Weather Station is now running automatically"
echo "Access it from any browser using:"
echo "http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status weather-station     # Check status"
echo "  sudo systemctl restart weather-station    # Restart"
echo "  sudo journalctl -u weather-station -f     # View live logs"
