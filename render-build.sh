#!/bin/bash

# ✅ Update & Install Chrome
apt-get update && apt-get install -y google-chrome-stable

# ✅ Install Python Dependencies
pip install --upgrade pip
pip install -r requirements.txt
