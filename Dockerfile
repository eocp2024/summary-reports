# Use a base image with Ubuntu
FROM ubuntu:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Firefox from APT
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    firefox \
    wget unzip curl \
    geckodriver \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt .

# Install Python dependencies (including Gunicorn & Selenium)
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Expose the necessary port (Railway dynamically assigns one)
EXPOSE 5000

# Run the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
