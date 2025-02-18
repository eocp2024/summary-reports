#!/bin/bash
# Render Build Script - Ensures all dependencies are correctly installed

# Use pre-installed Chromium path on Render
export CHROMIUM_PATH="/usr/bin/chromium"

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Inform Render that the build is complete
echo "✅ Build completed successfully!"
