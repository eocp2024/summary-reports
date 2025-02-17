#!/bin/bash

# Update package lists
apt-get update && apt-get install -y wget unzip curl

# Install Google Chrome
wget -qO- https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list
apt-get update && apt-get install -y google-chrome-stable

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
