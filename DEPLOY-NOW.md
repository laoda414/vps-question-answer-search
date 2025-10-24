# Ready to Deploy! 🚀

Your application is ready for deployment to VPS.

## ✅ What's Done

1. **GitHub Repository Created**: https://github.com/laoda414/vps-question-answer-search
2. **All Code Pushed**: Application code is on GitHub (NO sensitive data)
3. **Docker Ready**: All Docker configurations created
4. **Deployment Scripts Ready**: Automated deployment scripts prepared
5. **Security Configured**: `.gitignore` excludes all sensitive data

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:
- [x] Code pushed to GitHub
- [ ] VPS access configured (SSH to translator-bot-vps)
- [ ] `.env.production` values ready (API keys, secrets, etc.)
- [ ] Database file ready to transfer
- [ ] Domain name (optional, for HTTPS)

## 🚀 Deployment Steps

### 1. Prepare Environment File

Create a `.env.production` file with your actual values:

```bash
# Generate secure keys
python3 -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

Save these keys and all other configuration (Telegram bot token, OpenRouter API key, etc.)

### 2. SSH to VPS and Clone Repository

```bash
# SSH to VPS
ssh translator-bot-vps

# Create project directory
sudo mkdir -p /opt/qa-investment-search
sudo chown claude-deploy:claude-deploy /opt/qa-investment-search

# Clone repository
cd /opt
git clone https://github.com/laoda414/vps-question-answer-search.git qa-investment-search
cd qa-investment-search

# Create production environment file
cp .env.production.example .env.production
nano .env.production  # Paste your actual values
```

### 3. Create Data Directories

```bash
# Still on VPS
mkdir -p data/add_contact_phrase/investment_analysis
mkdir -p backups
mkdir -p logs
mkdir -p nginx/ssl nginx/logs
```

### 4. Transfer Database (From Local Machine)

**IMPORTANT: Do this from your LOCAL machine, NOT on VPS!**

```bash
# From LOCAL machine terminal
scp data/qa_search.db translator-bot-vps:/opt/qa-investment-search/data/

# Transfer investment analysis data
scp data/add_contact_phrase/investment_analysis/*.json \
  translator-bot-vps:/opt/qa-investment-search/data/add_contact_phrase/investment_analysis/
```

### 5. Choose Deployment Mode

#### Option A: HTTP Only (Quick Test)

```bash
# On VPS
cd /opt/qa-investment-search

# Use HTTP-only nginx config
cp nginx/conf.d/qa-search-http-only.conf.example nginx/conf.d/qa-search.conf

# Update with VPS IP
sed -i 's/your-domain.com/185.182.187.155/g' nginx/conf.d/qa-search.conf

# Deploy
./scripts/deployment/deploy-from-github.sh
```

Access at: **http://185.182.187.155**

#### Option B: HTTPS with SSL (Production)

```bash
# On VPS
cd /opt/qa-investment-search

# Setup SSL (requires domain name)
./scripts/deployment/setup-ssl.sh
# Enter your domain name and email when prompted

# Deploy
./scripts/deployment/deploy-from-github.sh
```

Access at: **https://your-domain.com**

### 6. Create Admin User

```bash
# Check Telegram bot is running
docker-compose -f docker-compose.prod.yml logs telegram-bot

# In Telegram, message your bot:
/start
/add_user admin YourSecurePassword123!
```

### 7. Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Test API
curl http://185.182.187.155/api/health

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 📚 Important Documentation

- **[DEPLOYMENT-DATA-TRANSFER.md](DEPLOYMENT-DATA-TRANSFER.md)** - Complete guide for data security and transfer
- **[DEPLOYMENT-GITHUB.md](DEPLOYMENT-GITHUB.md)** - Full GitHub deployment guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - General deployment reference

## 🔒 Security Reminders

- ✅ Database is NOT on GitHub (verified)
- ✅ `.env.production` is NOT on GitHub (verified)
- ⚠️  Database transfers via SSH/SCP only
- ⚠️  Never commit `.env.production` to git
- ⚠️  Use strong passwords for all user accounts

## 🛠️ Post-Deployment

### Update Application

```bash
# LOCAL: Make changes and push
git add .
git commit -m "Your changes"
git push

# VPS: Deploy updates
ssh translator-bot-vps "cd /opt/qa-investment-search && ./scripts/deployment/deploy-from-github.sh"
```

### Update Database

```bash
# LOCAL: Transfer updated database
scp data/qa_search.db translator-bot-vps:/opt/qa-investment-search/data/

# VPS: Restart backend
ssh translator-bot-vps "cd /opt/qa-investment-search && docker-compose -f docker-compose.prod.yml restart backend"
```

## 📞 Quick Commands

```bash
# View logs
ssh translator-bot-vps "cd /opt/qa-investment-search && docker-compose -f docker-compose.prod.yml logs -f"

# Restart all services
ssh translator-bot-vps "cd /opt/qa-investment-search && docker-compose -f docker-compose.prod.yml restart"

# Backup database
ssh translator-bot-vps "cd /opt/qa-investment-search && cp data/qa_search.db backups/backup_\$(date +%Y%m%d).db"

# Stop services
ssh translator-bot-vps "cd /opt/qa-investment-search && docker-compose -f docker-compose.prod.yml down"
```

## ✨ You're Ready!

Everything is prepared. Follow the steps above to deploy your application to the VPS.

**Repository**: https://github.com/laoda414/vps-question-answer-search
**VPS IP**: 185.182.187.155
**SSH**: translator-bot-vps
