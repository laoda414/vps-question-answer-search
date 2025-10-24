# Quick Reference Guide

## Common Commands

### Start Services Locally

```bash
# Terminal 1: Backend
cd backend && python app.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Telegram Bot
cd telegram_bot && python bot.py
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Restart a service
docker-compose restart [service_name]

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose build && docker-compose up -d
```

### Database Operations

```bash
# Recreate database
python scripts/init_db.py

# Backup database
cp data/qa_search.db data/qa_search_backup_$(date +%Y%m%d).db

# Check database size
ls -lh data/qa_search.db

# Open database in SQLite
sqlite3 data/qa_search.db
```

### Translation Operations

```bash
# Re-translate all data
python scripts/translate_qa.py

# Clear translation cache
rm data/translation_cache.json

# Check translation progress
tail -f logs/app.log
```

## Telegram Bot Commands

### User Management
```
/add_user john SecurePass123    # Add new user
/list_users                      # Show all users
/remove_user john                # Delete user
/reset_password john NewPass456  # Change password
```

### System Info
```
/stats    # Show database statistics
/help     # Show all commands
```

## API Examples

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "password"}'
```

### Search
```bash
curl "http://localhost:5000/api/search?q=amor&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Filters
```bash
curl http://localhost:5000/api/search/filters \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Export Results
```bash
curl "http://localhost:5000/api/export?q=amor&format=csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o results.csv
```

## File Locations

```
Configuration:
  .env                              # Environment variables

Data:
  data/qa_search.db                 # Main database
  data/normalized_qa_pairs.json     # Normalized data
  data/translated_qa_pairs.json     # Translated data
  data/translation_cache.json       # Translation cache

Logs:
  logs/app.log                      # Application logs

Source Data:
  data/add_contact_phrase/processed_chats/  # Original JSON files
```

## Environment Variables

```bash
# Required
TELEGRAM_BOT_TOKEN=              # From @BotFather
ADMIN_TELEGRAM_USER_ID=          # Your Telegram ID
OPENROUTER_API_KEY=              # OpenRouter API key

# Security (generate with: python -c "import secrets; print(secrets.token_hex(32))")
FLASK_SECRET_KEY=                # Random secret for Flask
JWT_SECRET_KEY=                  # Random secret for JWT

# Optional (has defaults)
MODEL_NAME=qwen/qwen3-235b-a22b-2507
TEMPERATURE=0.3
MAX_TOKENS=1000
PORT=5000
HOST=0.0.0.0
```

## Troubleshooting Quick Fixes

### Database Locked
```bash
# Check for running processes
ps aux | grep python

# Kill all Python processes (BE CAREFUL!)
pkill -9 python

# Restart services
```

### Frontend Can't Connect
```bash
# Check backend is running
curl http://localhost:5000/api/health

# Check vite proxy config
cat frontend/vite.config.js
```

### Telegram Bot Not Working
```bash
# Verify token
echo $TELEGRAM_BOT_TOKEN

# Check logs
cd telegram_bot && python bot.py
```

### Port Already in Use
```bash
# Find process on port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

## Performance Monitoring

### Check Database Size
```bash
du -h data/qa_search.db
```

### Count Records
```bash
sqlite3 data/qa_search.db "SELECT COUNT(*) FROM qa_pairs;"
```

### Check API Response Time
```bash
time curl "http://localhost:5000/api/search?q=amor"
```

## Backup & Restore

### Backup
```bash
# Database
cp data/qa_search.db backups/qa_search_$(date +%Y%m%d_%H%M%S).db

# Entire data directory
tar -czf backups/data_$(date +%Y%m%d).tar.gz data/

# Environment config
cp .env backups/.env.backup
```

### Restore
```bash
# Database
cp backups/qa_search_20250124.db data/qa_search.db

# Data directory
tar -xzf backups/data_20250124.tar.gz
```

## Update & Maintenance

### Update Dependencies
```bash
# Python
pip install -r backend/requirements.txt --upgrade
pip install -r scripts/requirements.txt --upgrade
pip install -r telegram_bot/requirements.txt --upgrade

# Node.js
cd frontend && npm update
```

### Clear Caches
```bash
# Translation cache
rm data/translation_cache.json

# Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Node modules (if needed)
cd frontend && rm -rf node_modules package-lock.json && npm install
```

### Check Logs
```bash
# Application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f

# Filter for errors
grep ERROR logs/app.log
```

## Development Tips

### Hot Reload
- Backend: Use `FLASK_ENV=development` in .env
- Frontend: `npm run dev` already has hot reload

### Debug Mode
```bash
# Backend debug mode
export FLASK_DEBUG=1
python backend/app.py

# Frontend with verbose logging
cd frontend && npm run dev -- --debug
```

### Test Translation
```python
# Quick test script
python -c "
from scripts.translate_qa import translate_batch, TranslationCache
from pathlib import Path
cache = TranslationCache(Path('data/translation_cache.json'))
result = translate_batch(['Oi, tudo bem?'], cache)
print(result)
"
```

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Health: http://localhost:5000/api/health

## Quick Test Checklist

- [ ] Login page loads
- [ ] Can login with valid credentials
- [ ] Search returns results
- [ ] Filters work correctly
- [ ] Pagination works
- [ ] Export CSV works
- [ ] Export JSON works
- [ ] Telegram bot responds
- [ ] Can add user via bot
- [ ] Translation cache exists

## Production Checklist

- [ ] Change all default secrets in .env
- [ ] Set FLASK_ENV=production
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Test concurrent users
- [ ] Monitor disk space
- [ ] Set up log rotation
- [ ] Document admin procedures
- [ ] Test disaster recovery

## Support Resources

- Setup Guide: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- Main README: [README.md](README.md)
- Docker Compose: [docker-compose.yml](docker-compose.yml)
