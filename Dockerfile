# Use a base image with Firefox pre-installed
FROM ubuntu:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
# Install dependencies and Firefox from APT
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    firefox \
    wget unzip \
    && apt-get clean\

# Install Geckodriver
RUN wget -q "https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-linux64.tar.gz" -O /tmp/geckodriver.tar.gz \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/geckodriver

# Set working directory
WORKDIR /app

# Copy project files **before installing dependencies**
COPY requirements.txt .

# **Install all Python dependencies, including Gunicorn**
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Expose the necessary port
EXPOSE 5000

# **Run the Flask app using Gunicorn**
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
