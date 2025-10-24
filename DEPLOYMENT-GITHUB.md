# QA Investment Search - GitHub Deployment Guide

This guide explains how to deploy the application to a VPS using GitHub as the code source.

## Overview

The deployment process:
1. Push code to GitHub repository
2. SSH to VPS
3. Pull latest code from GitHub
4. Build and deploy with Docker Compose

## Prerequisites

### Local Machine
- Git installed and configured
- GitHub account with repository access
- SSH access to VPS

### VPS (Already Setup)
- ✅ Docker and Docker Compose installed
- ✅ User: `claude-deploy` with docker permissions
- ✅ Project directory: `/opt/qa-investment-search`
- ✅ SSH alias: `translator-bot-vps`

## Initial Setup

### 1. Initialize Git Repository (Local)

```bash
# In your project directory
cd /home/dino/code/vps-question-answer-search

# Initialize git if not already done
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: QA Investment Search application"
```

### 2. Create GitHub Repository

```bash
# Using GitHub CLI (already logged in)
gh repo create vps-question-answer-search --public --source=. --remote=origin

# Or create manually on GitHub web interface and then:
git remote add origin https://github.com/YOUR_USERNAME/vps-question-answer-search.git
```

### 3. Push to GitHub

```bash
git branch -M main
git push -u origin main
```

### 4. Setup VPS Environment

```bash
# SSH to VPS
ssh translator-bot-vps

# Create project directory if it doesn't exist
sudo mkdir -p /opt/qa-investment-search
sudo chown claude-deploy:claude-deploy /opt/qa-investment-search

# Clone repository
cd /opt
git clone https://github.com/YOUR_USERNAME/vps-question-answer-search.git qa-investment-search
cd qa-investment-search
```

### 5. Configure Production Environment

```bash
# Still on VPS
cd /opt/qa-investment-search

# Create production environment file
cp .env.production.example .env.production

# Edit with your actual values
nano .env.production
```

**Required Configuration:**

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_actual_bot_token
ADMIN_TELEGRAM_USER_ID=your_telegram_id

# OpenRouter API
OPENROUTER_API_KEY=your_actual_api_key

# Security (generate new random keys!)
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Domain (if using SSL)
DOMAIN=your-domain.com

# API URL for frontend
VITE_API_URL=/api
```

### 6. Initialize Fresh Database

**IMPORTANT: DO NOT transfer the development database as it contains client data!**

The VPS will start with a fresh, empty database. You'll create new users via the Telegram bot.

```bash
# On VPS - the database will be created automatically on first run
# Located at: /opt/qa-investment-search/data/qa_search.db
```

### 7. Update Deployment Script

```bash
# On VPS, edit the GitHub URL in the script
nano /opt/qa-investment-search/scripts/deployment/deploy-from-github.sh

# Update this line:
GITHUB_REPO="https://github.com/YOUR_USERNAME/vps-question-answer-search.git"
```

## Deployment Process

### First Deployment

```bash
# SSH to VPS
ssh translator-bot-vps

# Navigate to project
cd /opt/qa-investment-search

# Run deployment
./scripts/deployment/deploy-from-github.sh
```

This script will:
- ✅ Backup database
- ✅ Pull latest code from GitHub
- ✅ Build Docker images
- ✅ Start containers
- ✅ Verify services are running

### Subsequent Deployments

Whenever you make changes:

```bash
# On LOCAL machine:
git add .
git commit -m "Your commit message"
git push origin main

# On VPS:
ssh translator-bot-vps
cd /opt/qa-investment-search
./scripts/deployment/deploy-from-github.sh
```

## Quick Deployment Workflow

```bash
# LOCAL: Make changes and push
git add .
git commit -m "Add investment analysis feature"
git push

# VPS: Deploy
ssh translator-bot-vps "cd /opt/qa-investment-search && ./scripts/deployment/deploy-from-github.sh"
```

## SSL/HTTPS Setup (Optional but Recommended)

### Using Let's Encrypt

```bash
# On VPS
ssh translator-bot-vps
cd /opt/qa-investment-search

# Run SSL setup script
./scripts/deployment/setup-ssl.sh

# Follow prompts:
# - Enter domain name
# - Enter email for notifications

# Redeploy with HTTPS
./scripts/deployment/deploy-from-github.sh
```

### HTTP Only (Quick Test)

```bash
# On VPS
cd /opt/qa-investment-search

# Use HTTP-only config
cp nginx/conf.d/qa-search-http-only.conf.example nginx/conf.d/qa-search.conf

# Update domain/IP
sed -i 's/your-domain.com/185.182.187.155/g' nginx/conf.d/qa-search.conf

# Deploy
./scripts/deployment/deploy-from-github.sh
```

## Managing the Application

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f telegram-bot
```

### Restart Services

```bash
# All services
docker-compose -f docker-compose.prod.yml restart

# Specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Stop Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### Check Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Access Container Shell

```bash
docker-compose -f docker-compose.prod.yml exec backend bash
```

## Initial User Setup

### Create Admin User via Telegram Bot

```bash
# Check if Telegram bot is running
docker-compose -f docker-compose.prod.yml logs telegram-bot

# In Telegram app, message your bot:
/start
/add_user admin SecurePassword123!
```

### Or Manually via CLI

```bash
ssh translator-bot-vps
cd /opt/qa-investment-search

# Run user creation script
docker-compose -f docker-compose.prod.yml exec backend python init_test_user.py
```

## Troubleshooting

### Deployment Failed

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Rebuild from scratch
docker-compose -f docker-compose.prod.yml down
docker system prune -a
./scripts/deployment/deploy-from-github.sh
```

### Services Won't Start

```bash
# Check if ports are available
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker
```

### Database Issues

```bash
# Restore from backup
cp backups/qa_search_TIMESTAMP.db data/qa_search.db
docker-compose -f docker-compose.prod.yml restart backend
```

### Pull Latest Code Manually

```bash
cd /opt/qa-investment-search
git fetch origin
git reset --hard origin/main
./scripts/deployment/deploy-from-github.sh
```

## Monitoring

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
df -h

# Docker disk usage
docker system df
```

### Logs Location

```bash
# Application logs
/opt/qa-investment-search/logs/

# Nginx logs
/opt/qa-investment-search/nginx/logs/

# Docker logs
docker-compose -f docker-compose.prod.yml logs
```

## Backup Strategy

### Automatic Backups

The deployment script automatically backs up the database before each deployment to:
```
/opt/qa-investment-search/backups/
```

Keeps only the last 10 backups.

### Manual Backup

```bash
# On VPS - Backup database
cp data/qa_search.db backups/manual_backup_$(date +%Y%m%d_%H%M%S).db

# Backup environment
cp .env.production backups/.env.production.backup

# Download to local machine (if needed)
# NOTE: Only do this if you need to backup production data
# DO NOT mix development and production databases
scp translator-bot-vps:/opt/qa-investment-search/backups/*.db ./prod-backups/
```

## Security Checklist

- [x] `.env.production` is in `.gitignore`
- [ ] Strong passwords for all user accounts
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] Regular backups scheduled
- [ ] Docker and system packages up to date
- [ ] Monitoring and alerting setup

## Quick Reference

```bash
# Deploy new version
git push && ssh translator-bot-vps "cd /opt/qa-investment-search && ./scripts/deployment/deploy-from-github.sh"

# View logs
ssh translator-bot-vps "cd /opt/qa-investment-search && docker-compose -f docker-compose.prod.yml logs -f"

# Restart services
ssh translator-bot-vps "cd /opt/qa-investment-search && docker-compose -f docker-compose.prod.yml restart"

# Backup database
ssh translator-bot-vps "cd /opt/qa-investment-search && cp data/qa_search.db backups/manual_$(date +%Y%m%d).db"
```

## Support

- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- API health: `curl http://YOUR-IP/api/health`
- Container status: `docker-compose -f docker-compose.prod.yml ps`
