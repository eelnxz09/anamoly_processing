# Deployment Guide

## Production Deployment Options

### Option 1: Docker Deployment (Recommended)

Create `Dockerfile` for backend:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=postgresql://user:password@db/anomaly_db
    depends_on:
      - db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: anomaly_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Deploy:
```bash
docker-compose up -d
```

### Option 2: Cloud Platforms

#### Heroku

**Backend:**
```bash
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create anomaly-detector-api
git push heroku main
```

**Frontend:**
```bash
# Build
npm run build

# Deploy to Netlify/Vercel
netlify deploy --prod --dir=dist
```

#### AWS EC2

1. Launch EC2 instance (Ubuntu 22.04)
2. Install dependencies:
```bash
sudo apt update
sudo apt install python3.9 python3-pip nginx nodejs npm
```

3. Clone and setup:
```bash
git clone your-repo
cd backend
pip3 install -r requirements.txt
```

4. Run with Gunicorn:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

5. Configure Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /var/www/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

#### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/anomaly-detector

# Deploy
gcloud run deploy anomaly-detector \
  --image gcr.io/PROJECT_ID/anomaly-detector \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 3: VPS Deployment

**Setup on Ubuntu/Debian VPS:**

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3.9 python3-pip nginx certbot python3-certbot-nginx

# 2. Clone repository
git clone your-repo
cd anomaly-detection-webapp

# 3. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Create systemd service
sudo nano /etc/systemd/system/anomaly-detector.service
```

Add:
```ini
[Unit]
Description=Anomaly Detector API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/venv/bin"
ExecStart=/path/to/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable anomaly-detector
sudo systemctl start anomaly-detector
```

**Setup frontend:**
```bash
cd ../frontend
npm install
npm run build

# Copy to nginx directory
sudo cp -r dist/* /var/www/html/
```

**Configure Nginx:**
```bash
sudo nano /etc/nginx/sites-available/anomaly-detector
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/anomaly-detector /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Add SSL with Let's Encrypt:**
```bash
sudo certbot --nginx -d your-domain.com
```

## Environment Configuration

**Production .env:**
```env
# Security
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=["https://your-domain.com"]

# Database
DATABASE_URL=postgresql://user:password@localhost/anomaly_db

# Paths (absolute)
DATA_WAREHOUSE_PATH=/var/lib/anomaly-detector/warehouse
UPLOAD_PATH=/var/lib/anomaly-detector/uploads
MODEL_PATH=/var/lib/anomaly-detector/models

# Performance
API_RELOAD=False
LOG_LEVEL=WARNING
```

## Database Setup (PostgreSQL)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE anomaly_db;
CREATE USER anomaly_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE anomaly_db TO anomaly_user;
\q

# Run migrations (if using SQLAlchemy)
cd backend
alembic upgrade head
```

## Monitoring & Maintenance

### Setup Logging

```python
# In main.py
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10000000,
    backupCount=5
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[handler]
)
```

### Health Checks

Setup monitoring:
```bash
# Create health check script
cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $response -ne 200 ]; then
    systemctl restart anomaly-detector
    echo "Service restarted at $(date)" >> /var/log/health-check.log
fi
EOF

chmod +x /usr/local/bin/health-check.sh

# Add to crontab
crontab -e
# Add: */5 * * * * /usr/local/bin/health-check.sh
```

### Backup Strategy

```bash
# Daily backup script
cat > /usr/local/bin/backup-data.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf /backups/warehouse-$DATE.tar.gz /var/lib/anomaly-detector/warehouse
find /backups -name "warehouse-*.tar.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-data.sh
# Add to crontab: 0 2 * * * /usr/local/bin/backup-data.sh
```

## Performance Optimization

### Backend

1. **Use Gunicorn with multiple workers:**
```bash
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

2. **Enable response caching:**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="anomaly-cache")
```

3. **Database connection pooling:**
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

### Frontend

1. **Enable compression in Nginx:**
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
```

2. **Cache static assets:**
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Enable HTTPS with SSL certificate
- [ ] Set up firewall (only ports 80, 443, 22)
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up fail2ban for SSH
- [ ] Regular security updates
- [ ] Database password encryption
- [ ] API authentication (if needed)

## Scaling

### Horizontal Scaling

Use load balancer (nginx):
```nginx
upstream backend {
    server 10.0.0.1:8000;
    server 10.0.0.2:8000;
    server 10.0.0.3:8000;
}

server {
    location /api {
        proxy_pass http://backend;
    }
}
```

### Database Scaling

- Read replicas for analytics queries
- Connection pooling
- Query optimization
- Indexed columns

### Caching Strategy

- Redis for API responses
- CDN for static assets
- Model caching in memory
- Warehouse query caching

## Cost Optimization

**Free Tier Options:**
- **Backend**: Railway, Render, Fly.io (free tier)
- **Frontend**: Netlify, Vercel, GitHub Pages (free)
- **Database**: Supabase, PlanetScale (free tier)
- **Storage**: Cloudflare R2, Backblaze B2 (free tier)

**Budget Setup (<$10/month):**
- DigitalOcean Droplet ($6/month)
- Cloudflare (free CDN)
- Backblaze B2 (storage)

## Troubleshooting

**Backend won't start:**
```bash
# Check logs
journalctl -u anomaly-detector -f

# Test manually
cd /path/to/backend
source venv/bin/activate
python main.py
```

**High memory usage:**
- Reduce worker count
- Enable model caching
- Limit concurrent requests
- Use smaller contamination value

**Slow predictions:**
- Use Isolation Forest (faster than SVM)
- Reduce PCA components
- Batch predictions
- Cache model in memory

---

**Questions? Open an issue on GitHub!**
