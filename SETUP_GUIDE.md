# QA Search Interface - Complete Setup Guide

This guide will walk you through setting up the QA Search Interface from scratch.

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenRouter API key
- Telegram Bot Token
- Your Telegram User ID

## Step 1: Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your credentials:
```bash
nano .env
```

Required values:
- `TELEGRAM_BOT_TOKEN` - Get from [@BotFather](https://t.me/botfather)
- `ADMIN_TELEGRAM_USER_ID` - Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot))
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `FLASK_SECRET_KEY` - Generate a random string
- `JWT_SECRET_KEY` - Generate another random string

Generate random secrets:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 2: Data Processing

### 2.1 Install Python Dependencies
```bash
cd scripts
pip install -r requirements.txt
```

### 2.2 Extract and Normalize Data
```bash
python scripts/process_data.py
```

This will:
- Parse all JSON files in `data/add_contact_phrase/processed_chats/`
- Extract QA pairs from both overall analysis and timeline progression
- Save normalized data to `data/normalized_qa_pairs.json`

Expected output:
```
Found 15 JSON files to process
Processing: analysis_260046_result.json
  Extracted 120 QA pairs
...
Total QA pairs extracted: 1500+
```

### 2.3 Translate QA Pairs
```bash
python scripts/translate_qa.py
```

This will:
- Translate all Portuguese texts to English using OpenRouter
- Cache translations to avoid re-processing
- Save translated data to `data/translated_qa_pairs.json`

**Important**: This step will consume API credits. The script will estimate the cost before starting.

Progress will be shown with progress bars:
```
Translating questions...
100%|████████████| 150/150 [02:30<00:00,  1.00it/s]

Translating answers...
100%|████████████| 150/150 [02:35<00:00,  0.97it/s]
```

### 2.4 Initialize Database
```bash
python scripts/init_db.py
```

This will:
- Create SQLite database with schema
- Enable WAL mode for concurrency
- Populate database with translated QA pairs
- Create FTS5 index for full-text search

Expected output:
```
Creating database at: data/qa_search.db
✅ Schema created successfully
✅ WAL mode enabled
✅ Database populated successfully

Database Statistics
=====================================
Total conversations: 15
Total QA pairs: 1,500
Total topics: 75
Date range: 2025-04-07 to 2025-05-12
```

## Step 3: User Management (Telegram Bot)

### 3.1 Install Dependencies
```bash
cd telegram_bot
pip install -r requirements.txt
```

### 3.2 Start the Bot
```bash
python bot.py
```

Expected output:
```
========================================
QA Search User Management Bot
========================================
Admin User ID: 123456789
Database: /path/to/qa_search.db
========================================
✅ Bot started successfully!
Send /start in Telegram to begin
```

### 3.3 Add Users via Telegram

Open your Telegram and send commands to your bot:

```
/start
/add_user john SecurePassword123
/list_users
```

Commands available:
- `/add_user <username> <password>` - Add new user
- `/list_users` - List all users
- `/remove_user <username>` - Remove user
- `/reset_password <username> <new_password>` - Reset password
- `/stats` - Show statistics

## Step 4: Start the Backend

### 4.1 Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4.2 Start the Server
```bash
python app.py
```

Expected output:
```
========================================
QA Search Backend
========================================
Database: data/qa_search.db
Host: 0.0.0.0
Port: 5000
Debug: False
========================================
 * Running on http://0.0.0.0:5000
```

The API will be available at `http://localhost:5000`

## Step 5: Start the Frontend

### 5.1 Install Dependencies
```bash
cd frontend
npm install
```

### 5.2 Start Development Server
```bash
npm run dev
```

Expected output:
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### 5.3 Access the Application

Open your browser and navigate to `http://localhost:3000`

You should see the login page. Use the credentials you created via the Telegram bot.

## Step 6: Testing

### 6.1 Test Search Functionality

1. Login with your credentials
2. Try searching for:
   - Portuguese words: "amor", "trabalho", "dinheiro"
   - English words: "love", "work", "money"
   - Phrases: "o que você acha"

3. Test filters:
   - Select date range
   - Filter by emotion (positive, negative, mixed)
   - Filter by specific conversation

4. Test export:
   - Click "Export CSV" to download results as CSV
   - Click "Export JSON" to download as JSON

### 6.2 Test Pagination

- Search should return 20 results per page
- Navigate through pages using the pagination controls

## Docker Deployment (Optional)

If you prefer to use Docker:

### Build and Run
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5000`

## Troubleshooting

### Database Not Found
```
❌ Error: Database not found
```
**Solution**: Make sure you've run `python scripts/init_db.py`

### Translation Fails
```
❌ Error during translation: ...
```
**Solutions**:
- Check your OpenRouter API key in `.env`
- Verify you have sufficient API credits
- Check your internet connection

### Frontend Can't Connect to Backend
**Solutions**:
- Make sure backend is running on port 5000
- Check `vite.config.js` proxy configuration
- Verify firewall is not blocking the connection

### Telegram Bot Not Responding
**Solutions**:
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check `ADMIN_TELEGRAM_USER_ID` matches your Telegram user ID
- Make sure bot is running (`python telegram_bot/bot.py`)

### SQLite Database Locked
```
sqlite3.OperationalError: database is locked
```
**Solution**: This usually means multiple processes are trying to write. Ensure only one instance of each service is running.

## Performance Tips

1. **Search Performance**:
   - FTS5 index provides fast full-text search
   - Results are paginated to reduce load
   - Use specific filters to narrow results

2. **Concurrency**:
   - SQLite WAL mode supports 5-7 concurrent readers
   - For your use case (10-15 users, 50% active), this is sufficient

3. **Caching**:
   - Translation cache prevents re-translating same texts
   - JWT tokens are valid for 24 hours

## Next Steps

1. **Add More Users**: Use Telegram bot to add all your team members
2. **Customize Frontend**: Edit colors in `frontend/tailwind.config.js`
3. **VPS Deployment**: Follow the deployment guide (when ready)
4. **Backup Database**: Set up regular backups of `data/qa_search.db`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs in `logs/app.log`
3. Check Docker logs: `docker-compose logs`

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Change default secret keys before production deployment
- Use strong passwords for all users
- Consider setting up HTTPS for production
- Regularly backup your database

## Maintenance

### Backup Database
```bash
# Create backup
cp data/qa_search.db data/qa_search_backup_$(date +%Y%m%d).db

# Or use SQLite backup command
sqlite3 data/qa_search.db ".backup data/qa_search_backup.db"
```

### Update Translation Cache
If you need to re-translate with a different model:
```bash
# Delete cache
rm data/translation_cache.json

# Edit .env to change MODEL_NAME
# Re-run translation
python scripts/translate_qa.py
```

### Add New Data
To add new conversation data:
1. Place new JSON files in `data/add_contact_phrase/processed_chats/`
2. Re-run data processing pipeline:
   ```bash
   python scripts/process_data.py
   python scripts/translate_qa.py
   python scripts/init_db.py  # Warning: This recreates the database
   ```

---

**Congratulations!** Your QA Search Interface is now fully set up and ready to use! 🎉
