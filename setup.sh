#!/bin/bash

# Exit script immediately if any command returns a non-zero status
set -e

echo "#==================================================#"
echo "🌤️ Technical Weather Station Setup for Raspberry Pi"
echo "#==================================================#"

# Dynamically fetch target paths to avoid hardcoded user errors
USER_HOME=$(eval echo "~$USER")
PROJECT_DIR="$USER_HOME/weather-station"

# Update system packages
echo "📦 Updating system packages safely..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Install required core development and python components 
echo "📦 Installing underlying OS dependencies..."
# 'python3-full' ensures venv handles pip isolation flawlessly under PEP 668
sudo apt-get install -y python3 python3-full git

# Initialize project structural paths
echo "📁 Structuring deployment directories..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Establish modern clean isolation parameters
echo "🤖 Building python isolated environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pipeline frameworks silently
pip install --quiet --upgrade pip
echo "📥 Injecting web micro-framework runtime dependencies..."
pip install --quiet flask requests

echo "✅ Python modules configured cleanly."

# Automate service layer initialization
echo "🔧 Crafting persistent systemd background context..."
sudo tee /etc/systemd/system/weather-station.service > /dev/null << EOF
[Unit]
Description=Weather Station Dashboard Engine
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/weatherapp.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Activate background worker process layers
echo "🔄 Initializing background workers..."
sudo systemctl daemon-reload
sudo systemctl enable weather-station.service
sudo systemctl restart weather-station.service

echo "=================================================="
echo "✅ Operational Setup Finalized Successfully!"
echo ""
echo "🌐 Interface Target Dashboard Endpoint:"
echo "👉 http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "⚙️ System Control Shortcuts:"
echo "  sudo systemctl status weather-station     # Check live state"
echo "  sudo journalctl -u weather-station -f     # Intercept live debug logs"
echo "=================================================="
