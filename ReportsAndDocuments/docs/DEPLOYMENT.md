# Deployment Guide

## Door Face Panels Smart Security System

Complete guide for deploying on edge devices (Raspberry Pi, Jetson Nano) and production environments.

---

## Prerequisites

- Python 3.8+
- Git
- pip package manager
- Virtual environment support

---

## Development Environment

### Local Setup

```bash
# Clone repository
git clone https://github.com/advitiyasharda/W26_4495_S3_AdvitiyaS.git
cd doortest

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

Access dashboard at: http://localhost:5000/

---

## Raspberry Pi Deployment

### Hardware Requirements

- Raspberry Pi 4 (4GB+ RAM recommended)
- 32GB microSD card
- Power supply (5V, 3A+)
- CSI Camera Module
- Network connectivity (Ethernet/WiFi)

### Step 1: Install Raspberry Pi OS

```bash
# Using Raspberry Pi Imager (recommended)
# Download from: https://www.raspberrypi.com/software/

# Write OS to microSD card and boot
```

### Step 2: System Preparation

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    libatlas-base-dev \
    libjasper-dev \
    libtiff5 \
    libjasper1 \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libopenjp2-7

# Install OpenCV dependencies
sudo apt-get install -y \
    libopenjp2-7 \
    libtiff5 \
    libjasper1 \
    libatlas-base-dev \
    libjasper-dev \
    libharfbuzz0b \
    libwebp6
```

### Step 3: Clone and Setup

```bash
# Clone repository
git clone https://github.com/advitiyasharda/W26_4495_S3_AdvitiyaS.git
cd doortest

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --no-cache-dir -r requirements.txt

# Note: This may take 15-30 minutes on Raspberry Pi
```

### Step 4: Configure Camera

```bash
# Enable camera interface
sudo raspi-config
# Navigate to: Interfacing Options > Camera > Enable

# Reboot
sudo reboot
```

### Step 5: Run Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run application
python main.py

# Or with Gunicorn (production)
gunicorn -w 2 -b 0.0.0.0:5000 main:app
```

### Step 6: Auto-start on Boot (Optional)

Create `/etc/systemd/system/doorface.service`:

```ini
[Unit]
Description=Door Face Panels Smart Security System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/doortest
Environment="PATH=/home/pi/doortest/venv/bin"
ExecStart=/home/pi/doortest/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable doorface.service
sudo systemctl start doorface.service

# Check status
sudo systemctl status doorface.service
```

---

## Jetson Nano Deployment

### Hardware Requirements

- Nvidia Jetson Nano Developer Kit
- Power supply (5V, 4A barrel connector recommended)
- microSD card (64GB+ recommended)
- CSI Camera Module
- Network connectivity

### Installation

```bash
# Install JetPack (includes CUDA, cuDNN)
# Download from: https://developer.nvidia.com/jetson-nano-developer-kit

# Flash to microSD using Etcher
# Boot and complete initial setup

# Enable GPU-optimized TensorFlow
pip install --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v46 \
    tensorflow-gpu==2.5.0

# Follow same steps as Raspberry Pi for additional setup
```

### Performance Optimization

```python
# In config.py
ENABLE_GPU = True
TARGET_DEVICE = 'jetson_nano'

# TensorFlow will automatically use GPU for inference
```

---

## Docker Deployment

### Docker Image

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libatlas-base-dev \
    libharfbuzz0b \
    libwebp6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
```

### Build and Run

```bash
# Build image
docker build -t doorface-system:latest .

# Run container
docker run -p 5000:5000 \
    -v /path/to/data:/app/data \
    -v /path/to/models:/app/models \
    --device /dev/video0:/dev/video0 \
    doorface-system:latest
```

---

## Production Deployment

### Using Gunicorn + Nginx

```bash
# Install Gunicorn
pip install gunicorn

# Install Nginx
sudo apt-get install nginx

# Configure Nginx (/etc/nginx/sites-available/doorface)
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /app/dashboard/static/;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/doorface /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Run Gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /var/log/doorface/access.log \
    --error-logfile /var/log/doorface/error.log \
    main:app
```

---

## Performance Tuning

### Raspberry Pi

```python
# config.py - Optimize for limited resources
ENABLE_GPU = False
ISOLATION_FOREST_N_ESTIMATORS = 50  # Reduce from 100
FACE_DETECTION_SCALE_FACTOR = 1.1   # Lower accuracy for speed
```

### Memory Management

```bash
# Monitor memory usage
free -h

# If memory constrained, reduce:
# - Number of concurrent workers
# - Model size/complexity
# - Database connection pool size
```

---

## Database Migration

### Backup

```bash
# SQLite backup
cp data/doorface.db data/doorface.db.backup

# Export to CSV
sqlite3 data/doorface.db ".mode csv" ".output backup.csv" "SELECT * FROM access_logs;"
```

### Migration to PostgreSQL (Future)

```python
# Update DATABASE_URI in config.py
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/doorface'

# Migration script would convert schema
```

---

## Monitoring & Logging

### Enable Detailed Logging

```python
# In main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/doorface.log'),
        logging.StreamHandler()
    ]
)
```

### System Monitoring

```bash
# Check API health
curl http://localhost:5000/api/health

# View logs
tail -f logs/doorface.log

# Monitor system resources
top
htop  # if installed
```

---

## Security Hardening

### Firewall Configuration

```bash
# UFW (Uncomplicated Firewall)
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS (if using SSL)
```

### SSL/TLS (Production)

```bash
# Install Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d yourdomain.com

# Update Nginx configuration with SSL
```

### Database Encryption

```bash
# Enable SQLite encryption (requires separate library)
# Future enhancement with SQLCipher
```

---

## Troubleshooting

### Camera Not Working

```bash
# Check camera connection
vcgencmd get_camera

# List USB devices
lsusb

# Check for errors
dmesg | grep camera
```

### Memory Issues

```bash
# Reduce worker processes
gunicorn -w 2 -b 0.0.0.0:5000 main:app

# Enable swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Network Connectivity

```bash
# Test connection
ping 8.8.8.8

# Check network interfaces
ifconfig

# Configure static IP (for remote deployment)
sudo nano /etc/dhcpcd.conf
```

---

## Performance Benchmarks

Target performance on Raspberry Pi 4:
- Facial Recognition: 85% accuracy, <500ms latency
- Anomaly Detection: <200ms inference time
- API Response: <100ms average

---

## Version Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart doorface.service
```

---

**Last Updated**: January 30, 2026  
**Version**: 0.1.0
