# 📦 Deployment Guide

Complete guide for deploying the AI Customer Support Automation system.

## 🏠 Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/YuvrajSinghBhadoria2/AI-Customer-Support-Automation.git
cd AI-Customer-Support-Automation

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start services
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# 5. Access services
# Dashboard: http://localhost:8501
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend

```bash
# 1. Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up database
# Install PostgreSQL and create database
createdb support_db

# 4. Configure environment
cp ../.env.example ../.env
# Edit .env with DATABASE_URL and API keys

# 5. Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Dashboard

```bash
# In a new terminal
cd dashboard
pip install -r requirements.txt

# Run dashboard
streamlit run app.py --server.port 8501
```

## 🔑 Gmail API Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2. Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure consent screen:
   - User Type: External (for testing) or Internal (for organization)
   - App name: "AI Support Automation"
   - Add scopes: `https://www.googleapis.com/auth/gmail.modify`
4. Create OAuth client ID:
   - Application type: Desktop app
   - Name: "Support Automation"
5. Download credentials JSON file
6. Rename to `credentials.json` and place in project root

### 3. First-Time Authentication

```bash
# Run backend - it will open browser for OAuth
cd backend
python -c "from app.services.gmail_service import gmail_service; gmail_service.authenticate()"

# Follow browser prompts to authorize
# This creates token.json for future use
```

### 4. Configure Support Email

In `.env`:

```bash
SUPPORT_EMAIL=support@yourdomain.com
```

## 🔐 Security Best Practices

### Production Checklist

- [ ] Use strong PostgreSQL password
- [ ] Enable SSL for database connections
- [ ] Restrict CORS origins in `backend/app/main.py`
- [ ] Use environment variables (never commit `.env`)
- [ ] Enable HTTPS for API and dashboard
- [ ] Rotate API keys regularly
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Use secrets management (AWS Secrets Manager, etc.)

### Environment Variables Security

```bash
# Never commit these files
.env
credentials.json
token.json
token.pickle
```

Add to `.gitignore` (already included).

## 🚀 Production Deployment

### Option 1: Docker on VPS

```bash
# 1. SSH into server
ssh user@your-server.com

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Clone repository
git clone https://github.com/YuvrajSinghBhadoria2/AI-Customer-Support-Automation.git
cd AI-Customer-Support-Automation

# 4. Configure environment
nano .env
# Add production values

# 5. Start services
docker-compose up -d

# 6. Set up reverse proxy (Nginx)
# See Nginx configuration below
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/support-automation

# API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Dashboard
server {
    listen 80;
    server_name dashboard.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/support-automation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com -d dashboard.yourdomain.com
```

### Option 2: Cloud Platforms

#### AWS (EC2 + RDS)

1. **Launch EC2 instance** (t3.medium recommended)
2. **Create RDS PostgreSQL** instance
3. **Update `.env`** with RDS endpoint
4. **Deploy** using Docker method above
5. **Configure** security groups for ports 80, 443, 8000, 8501

#### Google Cloud (Cloud Run)

1. **Build containers**:
   ```bash
   docker build -f Dockerfile.backend -t gcr.io/PROJECT_ID/support-backend .
   docker build -f Dockerfile.dashboard -t gcr.io/PROJECT_ID/support-dashboard .
   ```

2. **Push to GCR**:
   ```bash
   docker push gcr.io/PROJECT_ID/support-backend
   docker push gcr.io/PROJECT_ID/support-dashboard
   ```

3. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy support-backend --image gcr.io/PROJECT_ID/support-backend
   gcloud run deploy support-dashboard --image gcr.io/PROJECT_ID/support-dashboard
   ```

4. **Set up Cloud SQL** for PostgreSQL

#### Heroku

```bash
# 1. Create apps
heroku create support-backend
heroku create support-dashboard

# 2. Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev -a support-backend

# 3. Set environment variables
heroku config:set GROQ_API_KEY=your_key -a support-backend

# 4. Deploy
git push heroku main
```

## 🔄 Updates & Maintenance

### Updating the System

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d
```

### Database Backups

```bash
# Backup
docker exec support_db pg_dump -U postgres support_db > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i support_db psql -U postgres support_db < backup_20240101.sql
```

### Monitoring

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f dashboard

# Check resource usage
docker stats

# Database size
docker exec support_db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('support_db'));"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Gmail Authentication Fails

**Solution**: Ensure `credentials.json` is in project root and run authentication:

```bash
python -c "from app.services.gmail_service import gmail_service; gmail_service.authenticate()"
```

#### 2. Database Connection Error

**Solution**: Check PostgreSQL is running and DATABASE_URL is correct:

```bash
docker-compose ps
# Ensure db service is healthy
```

#### 3. Groq API Rate Limits

**Solution**: Implement retry logic or upgrade Groq plan. Current implementation has basic error handling.

#### 4. Dashboard Not Loading

**Solution**: Check backend is running and accessible:

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# Backend logs
docker-compose logs backend

# Dashboard logs
docker-compose logs dashboard

# Database logs
docker-compose logs db
```

## 📊 Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_urgency ON tickets(urgency);
CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC);
```

### Scaling

- **Horizontal**: Run multiple backend instances behind load balancer
- **Vertical**: Increase container resources in `docker-compose.yml`
- **Database**: Use connection pooling (already configured in SQLAlchemy)

## 🔒 Compliance

### GDPR Considerations

- Customer emails stored in database
- Implement data retention policy
- Add data export/deletion endpoints
- Update privacy policy

### Data Retention

```sql
-- Delete tickets older than 90 days
DELETE FROM tickets WHERE created_at < NOW() - INTERVAL '90 days';
```

## 📞 Support

For deployment issues:

- Check [GitHub Issues](https://github.com/YuvrajSinghBhadoria2/AI-Customer-Support-Automation/issues)
- Review logs: `docker-compose logs -f`
- Verify environment variables: `docker-compose config`

---

**Ready for production?** Follow this guide step-by-step and you'll have a robust AI support system running in under 30 minutes! 🚀
