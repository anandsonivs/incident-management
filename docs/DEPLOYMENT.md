# Deployment Guide

## Overview

This guide covers deploying the Incident Management System in various environments, from development to production. The system supports multiple deployment strategies including Docker, cloud platforms, and traditional server deployments.

## Prerequisites

### System Requirements
- **Python**: 3.11+
- **Database**: PostgreSQL 13+ (production) or SQLite (development)
- **Memory**: Minimum 512MB RAM
- **Storage**: Minimum 1GB free space
- **Network**: HTTP/HTTPS access

### Software Dependencies
- **Python packages**: See `requirements.txt`
- **Database**: PostgreSQL with connection pooling
- **Web server**: Nginx (recommended for production)
- **Process manager**: Supervisor or systemd
- **SSL certificates**: For HTTPS in production

## Environment Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/incident_management
SQLALCHEMY_DATABASE_URL=postgresql://user:password@localhost/incident_management

# Security
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_V1_STR=/v1
PROJECT_NAME=Incident Management System
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Environment
ENV=production
ENVIRONMENT=production
LOG_LEVEL=INFO

# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Optional: SMS Configuration
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890
```

### Database Setup

#### PostgreSQL (Production)

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib

   # CentOS/RHEL
   sudo yum install postgresql postgresql-server
   sudo postgresql-setup initdb
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **Create Database and User**
   ```bash
   sudo -u postgres psql
   
   CREATE DATABASE incident_management;
   CREATE USER incident_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE incident_management TO incident_user;
   ALTER USER incident_user CREATEDB;
   \q
   ```

3. **Configure Connection Pooling**
   ```bash
   # Install pgBouncer for connection pooling
   sudo apt-get install pgbouncer
   
   # Configure pgBouncer
   sudo nano /etc/pgbouncer/pgbouncer.ini
   ```

#### SQLite (Development)

For development, SQLite is automatically configured:
```bash
# No additional setup required
# Database file will be created automatically
```

## Deployment Methods

### 1. Docker Deployment (Recommended)

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://incident_user:secure_password@db:5432/incident_management
      - SECRET_KEY=your-secret-key
      - ENV=production
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=incident_management
      - POSTGRES_USER=incident_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Deployment Commands
```bash
# Build and start services
docker-compose up -d

# Run database migrations
docker-compose exec app alembic upgrade head

# Check logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### 2. Traditional Server Deployment

#### Systemd Service
Create `/etc/systemd/system/incident-management.service`:

```ini
[Unit]
Description=Incident Management System
After=network.target postgresql.service

[Service]
Type=exec
User=incident
Group=incident
WorkingDirectory=/opt/incident-management
Environment=PATH=/opt/incident-management/venv/bin
ExecStart=/opt/incident-management/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration
Create `/etc/nginx/sites-available/incident-management`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/incident-management.crt;
    ssl_certificate_key /etc/ssl/private/incident-management.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /opt/incident-management/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Deployment Script
```bash
#!/bin/bash
# deploy.sh

set -e

# Configuration
APP_DIR="/opt/incident-management"
APP_USER="incident"
APP_GROUP="incident"

echo "Starting deployment..."

# Create user if not exists
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
fi

# Create application directory
sudo mkdir -p "$APP_DIR"
sudo chown "$APP_USER:$APP_GROUP" "$APP_DIR"

# Clone/update code
sudo -u "$APP_USER" git clone https://github.com/your-repo/incident-management.git "$APP_DIR" || \
sudo -u "$APP_USER" git -C "$APP_DIR" pull

# Setup virtual environment
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Setup environment
sudo -u "$APP_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
# Edit .env file with production values

# Run database migrations
sudo -u "$APP_USER" "$APP_DIR/venv/bin/alembic" -c "$APP_DIR/alembic.ini" upgrade head

# Setup systemd service
sudo cp "$APP_DIR/deploy/incident-management.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable incident-management

# Setup Nginx
sudo cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/incident-management
sudo ln -sf /etc/nginx/sites-available/incident-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Start application
sudo systemctl start incident-management

echo "Deployment completed successfully!"
```

### 3. Cloud Platform Deployment

#### AWS ECS/Fargate

**Task Definition:**
```json
{
  "family": "incident-management",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/incident-management-task-role",
  "containerDefinitions": [
    {
      "name": "incident-management",
      "image": "your-registry/incident-management:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:password@your-rds-endpoint:5432/incident_management"
        },
        {
          "name": "SECRET_KEY",
          "value": "your-secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/incident-management",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Google Cloud Run

**Dockerfile for Cloud Run:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run expects the app to listen on $PORT
ENV PORT=8000

CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Deploy Command:**
```bash
# Build and push image
docker build -t gcr.io/your-project/incident-management .
docker push gcr.io/your-project/incident-management

# Deploy to Cloud Run
gcloud run deploy incident-management \
  --image gcr.io/your-project/incident-management \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="postgresql://user:password@host:5432/db" \
  --set-env-vars SECRET_KEY="your-secret-key"
```

## Database Migrations

### Running Migrations

```bash
# Check current migration status
alembic current

# Apply pending migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Rollback migration
alembic downgrade -1
```

### Migration Best Practices

1. **Always backup before migrations**
   ```bash
   pg_dump incident_management > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Test migrations in staging first**
3. **Use transaction wrapping for safety**
4. **Monitor migration performance**

## SSL/TLS Configuration

### Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Self-Signed Certificate (Development)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/incident-management.key \
  -out /etc/ssl/certs/incident-management.crt
```

## Monitoring and Logging

### Application Logging

Configure logging in your application:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### System Monitoring

#### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Add to your FastAPI app
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_LATENCY.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest())
```

#### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": "connected" if check_db_connection() else "disconnected"
    }
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/incident-management"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

mkdir -p "$BACKUP_DIR"

# Create backup
pg_dump incident_management > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE.gz"
```

### Automated Backup with Cron

```bash
# Add to crontab
0 2 * * * /opt/incident-management/scripts/backup.sh
```

### Recovery

```bash
# Restore from backup
gunzip -c backup_20250828_020000.sql.gz | psql incident_management
```

## Security Considerations

### Production Security Checklist

- [ ] Use strong, unique SECRET_KEY
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure proper CORS origins
- [ ] Use environment variables for sensitive data
- [ ] Implement rate limiting
- [ ] Regular security updates
- [ ] Database connection encryption
- [ ] File permissions (600 for .env, 755 for app)
- [ ] Firewall configuration
- [ ] Regular backups

### Security Headers

Add security headers in Nginx:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

## Performance Optimization

### Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX idx_incidents_team_id ON incidents(team_id);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_created_at ON incidents(created_at);
CREATE INDEX idx_escalation_events_incident_id ON escalation_events(incident_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
```

### Application Optimization

```python
# Enable connection pooling
DATABASE_URL = "postgresql://user:password@host:5432/db?pool_size=20&max_overflow=30"

# Use async database operations
from sqlalchemy.ext.asyncio import create_async_engine
```

### Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# Configure Redis caching
FastAPICache.init(RedisBackend(redis), prefix="incident-management")
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
psql -h localhost -U incident_user -d incident_management -c "SELECT 1;"

# Check connection pool
SELECT * FROM pg_stat_activity WHERE datname = 'incident_management';
```

#### Application Startup Issues
```bash
# Check logs
sudo journalctl -u incident-management -f

# Check configuration
python -c "from app.core.config import get_settings; print(get_settings())"
```

#### Performance Issues
```bash
# Check database performance
SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

# Check application metrics
curl http://localhost:8000/metrics
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
export DEBUG=1
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload --log-level debug
```

## Maintenance

### Regular Maintenance Tasks

1. **Database maintenance**
   ```sql
   VACUUM ANALYZE;
   REINDEX DATABASE incident_management;
   ```

2. **Log rotation**
   ```bash
   logrotate /etc/logrotate.d/incident-management
   ```

3. **Security updates**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **Backup verification**
   ```bash
   # Test backup restoration
   gunzip -c backup_file.sql.gz | psql test_db
   ```

### Monitoring Alerts

Set up monitoring alerts for:
- Application availability
- Database connectivity
- Disk space usage
- Memory usage
- Error rates
- Response times

---

**Last Updated:** August 2025  
**Version:** 1.0.0  
**Test Status:** 83.3% passing (15/18 tests)
