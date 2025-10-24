# Database and Data Transfer Guide

## IMPORTANT: Data Security

⚠️ **CLIENT DATA IS NEVER STORED ON GITHUB!**

- GitHub repository contains **ONLY CODE** (no database, no .env files, no client data)
- Database is transferred **DIRECTLY** from local machine to VPS via SSH/SCP
- `.gitignore` is configured to exclude all data files

## What Goes Where

### GitHub (Public Repository)
✅ Application code
✅ Docker configurations
✅ Deployment scripts
✅ Documentation
✅ `.env.example` files (templates only)

❌ Database files (`*.db`)
❌ Environment files (`.env`, `.env.production`)
❌ Client data
❌ Translation cache
❌ Logs
❌ Backups
❌ SSL certificates

### VPS (Private Server)
✅ All code (pulled from GitHub)
✅ Database (transferred from local machine)
✅ `.env.production` (created manually on VPS)
✅ Client data
✅ Backups

## Deployment Process

### Step 1: Deploy Code via GitHub

```bash
# On LOCAL machine - Push code to GitHub
git add .
git commit -m "Update application"
git push origin main

# On VPS - Pull and deploy code
ssh translator-bot-vps
cd /opt/qa-investment-search
./scripts/deployment/deploy-from-github.sh
```

### Step 2: Transfer Database Directly to VPS

**IMPORTANT: Do this via SSH/SCP, NOT GitHub!**

```bash
# From LOCAL machine - Transfer database to VPS
scp data/qa_search.db translator-bot-vps:/opt/qa-investment-search/data/

# Verify transfer
ssh translator-bot-vps "ls -lh /opt/qa-investment-search/data/qa_search.db"
```

### Step 3: Transfer Investment Analysis Data (if needed)

```bash
# From LOCAL machine - Transfer investment analysis JSON files
scp -r data/add_contact_phrase/investment_analysis/*.json \
  translator-bot-vps:/opt/qa-investment-search/data/add_contact_phrase/investment_analysis/

# Verify transfer
ssh translator-bot-vps "ls -lh /opt/qa-investment-search/data/add_contact_phrase/investment_analysis/"
```

## Complete First-Time Deployment

### 1. Prepare Local Environment

```bash
# Ensure all data is ready
ls -lh data/qa_search.db
ls -lh data/add_contact_phrase/investment_analysis/
```

### 2. Push Code to GitHub

```bash
# Check what will be committed (should NOT include data files)
git status
git add .
git commit -m "Deploy to production"
git push origin main
```

### 3. Setup VPS and Pull Code

```bash
# SSH to VPS
ssh translator-bot-vps

# Create project directory
sudo mkdir -p /opt/qa-investment-search
sudo chown claude-deploy:claude-deploy /opt/qa-investment-search

# Clone repository
cd /opt
git clone https://github.com/YOUR_USERNAME/vps-question-answer-search.git qa-investment-search
cd qa-investment-search

# Create production environment
cp .env.production.example .env.production
nano .env.production  # Fill in actual values
```

### 4. Create Data Directories on VPS

```bash
# Still on VPS
mkdir -p /opt/qa-investment-search/data/add_contact_phrase/investment_analysis
mkdir -p /opt/qa-investment-search/backups
mkdir -p /opt/qa-investment-search/logs
```

### 5. Transfer Database from Local to VPS

```bash
# From LOCAL machine (NOT on VPS!)
scp data/qa_search.db translator-bot-vps:/opt/qa-investment-search/data/
```

### 6. Transfer Investment Analysis Data

```bash
# From LOCAL machine
scp data/add_contact_phrase/investment_analysis/*.json \
  translator-bot-vps:/opt/qa-investment-search/data/add_contact_phrase/investment_analysis/
```

### 7. Deploy Application on VPS

```bash
# On VPS
ssh translator-bot-vps
cd /opt/qa-investment-search
./scripts/deployment/deploy-from-github.sh
```

## Updating Data on VPS

### Update Database Only

```bash
# From LOCAL machine
# 1. Backup existing VPS database first
ssh translator-bot-vps "cp /opt/qa-investment-search/data/qa_search.db /opt/qa-investment-search/backups/before_update_\$(date +%Y%m%d_%H%M%S).db"

# 2. Transfer new database
scp data/qa_search.db translator-bot-vps:/opt/qa-investment-search/data/

# 3. Restart backend
ssh translator-bot-vps "cd /opt/qa-investment-search && docker-compose -f docker-compose.prod.yml restart backend"
```

### Update Investment Analysis Data

```bash
# From LOCAL machine
scp data/add_contact_phrase/investment_analysis/*.json \
  translator-bot-vps:/opt/qa-investment-search/data/add_contact_phrase/investment_analysis/

# Restart backend to refresh data
ssh translator-bot-vps "cd /opt/qa-investment-search && docker-compose -f docker-compose.prod.yml restart backend"
```

## Verify Data is NOT on GitHub

### Before Pushing to GitHub, Check:

```bash
# Check git status (should NOT show any .db or data files)
git status

# Check what will be committed
git diff --cached

# Verify .gitignore is working
git check-ignore data/qa_search.db  # Should output the path if ignored
git check-ignore data/  # Should output the path if ignored
git check-ignore .env.production  # Should output the path if ignored
```

### If Data Accidentally Added:

```bash
# Remove from staging
git reset HEAD data/
git reset HEAD *.db
git reset HEAD .env.production

# Make sure .gitignore is correct
cat .gitignore | grep -E "(data/|*.db|.env)"
```

## Security Checklist

Before deploying:
- [ ] `.gitignore` excludes `data/`, `*.db`, `.env.production`
- [ ] `git status` shows NO database files
- [ ] Test with: `git check-ignore data/qa_search.db` (should output path)
- [ ] Database transferred via SCP, NOT GitHub
- [ ] `.env.production` created manually on VPS, NOT committed to GitHub
- [ ] GitHub repository is public but contains NO sensitive data

## Data Backup Strategy

### VPS to Local (Backup Production Data)

```bash
# Download production database to local for backup
scp translator-bot-vps:/opt/qa-investment-search/data/qa_search.db \
  ./backups/prod_backup_$(date +%Y%m%d_%H%M%S).db

# Download VPS backups
scp -r translator-bot-vps:/opt/qa-investment-search/backups/* \
  ./prod-backups/
```

### Separate Dev and Production Data

```
Local Machine:
  data/qa_search.db                    # Development database
  backups/                             # Development backups
  prod-backups/                        # Production backups (from VPS)

VPS:
  /opt/qa-investment-search/data/      # Production database
  /opt/qa-investment-search/backups/   # Production backups
```

## Quick Reference

```bash
# Push code changes
git push origin main

# Deploy code to VPS
ssh translator-bot-vps "cd /opt/qa-investment-search && ./scripts/deployment/deploy-from-github.sh"

# Update database on VPS
scp data/qa_search.db translator-bot-vps:/opt/qa-investment-search/data/

# Backup VPS database to local
scp translator-bot-vps:/opt/qa-investment-search/data/qa_search.db ./prod-backups/backup_$(date +%Y%m%d).db

# Check what's being tracked by git
git status

# Verify data is ignored
git check-ignore data/
```
