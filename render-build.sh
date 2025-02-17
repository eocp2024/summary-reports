#!/bin/bash

# Install dependencies
apt-get update && apt-get install -y wget unzip curl firefox-esr

# Install ChromeDriver for Selenium
wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
dpkg -i google-chrome-stable_current_amd64.deb || apt-get install -fy

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
