# QA Investment Search - Deployment Guide

## Prerequisites

- VPS with Docker and Docker Compose installed
- Domain name (optional, for HTTPS)
- SSH access to the VPS

## VPS Details

```
Host: 185.182.187.155
User: claude-deploy
SSH Alias: translator-bot-vps
Project Directory: /opt/qa-investment-search
```

## Quick Deployment Steps

### 1. Prepare Local Environment

```bash
# Copy production environment template
cp .env.production.example .env.production

# Edit and fill in all required values
nano .env.production
```

**Important values to change:**
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `ADMIN_TELEGRAM_USER_ID` - Your Telegram user ID
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `FLASK_SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `JWT_SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `DOMAIN` - Your domain name (if using HTTPS)
- `VITE_API_URL` - Set to `/api` for production

### 2. Transfer Files to VPS

```bash
# From your local machine
rsync -avz --exclude 'venv' \
           --exclude 'node_modules' \
           --exclude '.git' \
           --exclude '*.pyc' \
           --exclude '__pycache__' \
           --exclude '.env' \
           . translator-bot-vps:/opt/qa-investment-search/
```

### 3. Deploy on VPS

#### Option A: HTTP Only (Quick Test)

```bash
# SSH into VPS
ssh translator-bot-vps

# Navigate to project directory
cd /opt/qa-investment-search

# Use HTTP-only nginx config
cp nginx/conf.d/qa-search-http-only.conf.example nginx/conf.d/qa-search.conf

# Update domain in config
sed -i 's/your-domain.com/185.182.187.155/g' nginx/conf.d/qa-search.conf

# Deploy
./scripts/deployment/deploy.sh
```

Access at: `http://185.182.187.155`

#### Option B: HTTPS with Let's Encrypt (Production)

```bash
# SSH into VPS
ssh translator-bot-vps

# Navigate to project directory
cd /opt/qa-investment-search

# Setup SSL certificate
./scripts/deployment/setup-ssl.sh

# Follow prompts to enter:
# - Domain name
# - Email for Let's Encrypt

# Deploy
./scripts/deployment/deploy.sh
```

Access at: `https://your-domain.com`

### 4. Initialize Database and Create Admin User

```bash
# SSH into VPS
ssh translator-bot-vps
cd /opt/qa-investment-search

# Copy your existing database or initialize new one
# If you have existing data:
docker cp ./data/qa_search.db qa-search-backend:/app/data/

# Start Telegram bot to create users
docker-compose -f docker-compose.prod.yml logs -f telegram-bot

# Use Telegram bot commands:
# /start - Show available commands
# /add_user <username> <password> - Create a user
```

## Docker Commands

```bash
# View all running containers
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f telegram-bot

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Execute command in container
docker-compose -f docker-compose.prod.yml exec backend bash
```

## Update/Redeploy

```bash
# SSH into VPS
ssh translator-bot-vps
cd /opt/qa-investment-search

# Pull latest code from local machine
# (run rsync command from step 2 again)

# Or if using git:
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# View logs to ensure everything started correctly
docker-compose -f docker-compose.prod.yml logs -f
```

## Backup Database

```bash
# Manual backup
docker cp qa-search-backend:/app/data/qa_search.db ./backup_$(date +%Y%m%d_%H%M%S).db

# Or use the built-in backup in deploy script
./scripts/deployment/deploy.sh  # Creates backup automatically
```

## Troubleshooting

### Check Service Health

```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# Check backend health
curl http://localhost/api/health

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Container Won't Start

```bash
# View detailed logs
docker-compose -f docker-compose.prod.yml logs backend

# Check if port is already in use
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Restart Docker service
sudo systemctl restart docker
```

### Database Issues

```bash
# Check database file exists and has correct permissions
docker-compose -f docker-compose.prod.yml exec backend ls -la /app/data/

# Copy database from backup
docker cp ./backups/qa_search_TIMESTAMP.db qa-search-backend:/app/data/qa_search.db
docker-compose -f docker-compose.prod.yml restart backend
```

### SSL Certificate Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Renew certificates
sudo certbot renew

# Copy new certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/qa-investment-search/nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/qa-investment-search/nginx/ssl/

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

## Security Recommendations

1. **Change default secrets** in `.env.production`
2. **Use strong passwords** for user accounts
3. **Keep Docker updated**: `sudo apt update && sudo apt upgrade`
4. **Enable firewall**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
5. **Regular backups** of database
6. **Monitor logs** regularly for suspicious activity
7. **Update SSL certificates** before expiration (auto-renewal recommended)

## Monitoring

### Resource Usage

```bash
# Check Docker container stats
docker stats

# Check disk usage
df -h

# Check memory usage
free -h
```

### Set Up Auto-Restart

Containers are configured with `restart: unless-stopped` so they will automatically restart on failure or server reboot.

## Support

For issues or questions, check:
- Container logs: `docker-compose -f docker-compose.prod.yml logs`
- System logs: `journalctl -u docker`
- Nginx logs: `tail -f nginx/logs/qa-search-error.log`
