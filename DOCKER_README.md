# 🐳 Docker Deployment Guide

## Quick Start

### Windows
```bash
docker-run.bat
```

### Linux/Mac
```bash
chmod +x docker-run.sh
./docker-run.sh
```

## Manual Docker Commands

### Build the Image
```bash
docker-compose build
```

### Start the Container
```bash
docker-compose up -d
```

### Stop the Container
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

### Restart Container
```bash
docker-compose restart
```

## Access the Application

Once running, access the web interface at:
- **Main Dashboard:** http://localhost:5000
- **Admin Panel:** http://localhost:5000/admin

Default admin password: `admin123`

## Configuration

### Telegram Bot Setup
1. Start the container
2. Access admin panel at http://localhost:5000/admin
3. Configure your Telegram bot token and chat IDs
4. Settings are persisted in `telegram_config.json`

### Camera Access

#### Windows
Docker Desktop automatically handles camera access. Make sure:
- Docker Desktop is running
- Camera permissions are granted to Docker

#### Linux
The container needs access to `/dev/video0`. If you have multiple cameras:
```yaml
devices:
  - /dev/video0:/dev/video0
  - /dev/video1:/dev/video1
```

#### Mac
Camera access in Docker on Mac requires additional setup:
1. Use Docker Desktop
2. Grant camera permissions in System Preferences

## Environment Variables

You can customize the deployment by editing `docker-compose.yml`:

```yaml
environment:
  - FLASK_ENV=production
  - ADMIN_PASSWORD=your_secure_password
  - EMERGENCY_THRESHOLD=3.0
  - MAX_ALERTS_PER_5MIN=5
```

## Volume Mounts

The following are mounted as volumes for persistence:
- `telegram_config.json` - Telegram configuration
- `eye_model.pt` - Eye detection model (if available)
- `yawn_model.pt` - Yawn detection model (if available)

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Check if port 5000 is already in use
netstat -ano | findstr :5000  # Windows
lsof -i :5000                  # Linux/Mac
```

### Camera not detected
```bash
# Check camera devices (Linux)
ls -l /dev/video*

# Test camera access
docker exec -it drowsiness-detection-system python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Permission denied errors (Linux)
```bash
# Add user to video group
sudo usermod -aG video $USER

# Restart Docker
sudo systemctl restart docker
```

## Production Deployment

For production use:

1. **Change default password** in admin panel
2. **Use HTTPS** with a reverse proxy (nginx/traefik)
3. **Set resource limits** in docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

4. **Enable logging**:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## GPU Support (Optional)

For better performance with NVIDIA GPU:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Update `docker-compose.yml`:
```yaml
services:
  drowsiness-detector:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

## Health Check

The container includes a health check that runs every 30 seconds:
```bash
# Check container health
docker ps
```

Look for "healthy" status in the STATUS column.

## Backup Configuration

```bash
# Backup telegram config
docker cp drowsiness-detection-system:/app/telegram_config.json ./backup/

# Restore telegram config
docker cp ./backup/telegram_config.json drowsiness-detection-system:/app/
```

## Support

For issues or questions:
- GitHub: https://github.com/vedraut00/real_time_drowsiness_locations
- Check logs: `docker-compose logs -f`
