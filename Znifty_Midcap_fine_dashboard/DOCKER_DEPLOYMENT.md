# Docker Deployment Guide

## Overview
This guide explains how to deploy the Nifty Midcap Fine Dashboard using Docker.

## Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (version 20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 1.29+)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Build and run the application:**
   ```bash
   docker-compose up -d
   ```

2. **Check logs:**
   ```bash
   docker-compose logs -f nifty-midcap-dashboard
   ```

3. **Access the application:**
   - Open your browser and navigate to: `http://localhost:5000`

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker CLI

1. **Build the image:**
   ```bash
   docker build -t nifty-midcap-dashboard:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name nifty-midcap \
     -p 5000:5000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs.log:/app/logs.log \
     -e PYTHONUNBUFFERED=1 \
     nifty-midcap-dashboard:latest
   ```

3. **Check container status:**
   ```bash
   docker ps
   ```

4. **View logs:**
   ```bash
   docker logs -f nifty-midcap
   ```

5. **Stop the container:**
   ```bash
   docker stop nifty-midcap
   ```

## Configuration

### Environment Variables
You can customize the following environment variables in `docker-compose.yml`:

```yaml
environment:
  - FLASK_ENV=production
  - PYTHONUNBUFFERED=1
  - FLASK_DEBUG=0
```

### Port Configuration
To change the exposed port, modify in `docker-compose.yml`:
```yaml
ports:
  - "8000:5000"  # Access on http://localhost:8000
```

### Volume Mounts
The following directories are mounted:
- `./data:/app/data` - Data files
- `./logs.log:/app/logs.log` - Application logs

## Production Deployment

### Security Best Practices
1. **Use environment variables for secrets:**
   ```yaml
   environment:
     - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
   ```

2. **Set proper resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 512M
       reservations:
         cpus: '0.5'
         memory: 256M
   ```

3. **Use a reverse proxy (Nginx):**
   - Uncomment the nginx service in `docker-compose.yml`
   - Configure SSL/TLS for HTTPS

### Scaling
For multiple instances behind a load balancer:
```bash
docker-compose up -d --scale nifty-midcap-dashboard=3
```

## Troubleshooting

### Container won't start
```bash
docker logs nifty-midcap-dashboard
```

### Port already in use
Change the port in `docker-compose.yml` or stop conflicting containers:
```bash
docker ps
docker stop <container_id>
```

### Permission issues
Ensure proper volume permissions:
```bash
chmod -R 755 data/
chmod 644 logs.log
```

### Memory issues
Increase Docker's memory allocation or modify `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
```

## Useful Commands

```bash
# View running containers
docker-compose ps

# Execute command in container
docker-compose exec nifty-midcap-dashboard python -c "print('test')"

# Rebuild image
docker-compose build --no-cache

# Remove stopped containers and unused images
docker system prune -a

# View real-time statistics
docker stats

# Copy files from container
docker cp nifty-midcap:/app/data/file.json ./local-file.json
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to Docker

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: docker/setup-buildx-action@v1
      - uses: docker/build-push-action@v2
        with:
          context: .
          push: true
          tags: myregistry/nifty-midcap:latest
```

## Support
For issues or questions, refer to:
- [Docker Documentation](https://docs.docker.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- Project README.md
