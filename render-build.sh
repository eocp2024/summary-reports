#!/bin/bash

# Update package list
apt-get update

# Install Firefox
apt-get install -y firefox

# Install GeckoDriver
GECKODRIVER_VERSION="v0.35.0"
wget -q "https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-linux64.tar.gz"
tar -xzf geckodriver-linux64.tar.gz
chmod +x geckodriver
mv geckodriver /usr/local/bin/

echo "GeckoDriver installed successfully!"
