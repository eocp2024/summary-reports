#!/bin/bash

# Exit on error
set -e  

# Install dependencies
sudo apt-get update && sudo apt-get install -y wget unzip curl firefox-esr

# Install Geckodriver
GECKO_VERSION="v0.35.0"
wget "https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/geckodriver-linux64.tar.gz"
tar -xvzf geckodriver-linux64.tar.gz
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
rm geckodriver-linux64.tar.gz
echo "✅ Geckodriver installed successfully!"

# Install Python dependencies
pip install -r requirements.txt

echo "✅ Render Build Script Completed!"
