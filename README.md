# QA Search Interface

AI-powered question-answer search interface with Portuguese-English translation support.

## Features

- 🔍 Bilingual search (Portuguese & English)
- 🤖 AI-powered translation using OpenRouter
- 🔐 Telegram bot authentication and user management
- 📊 Advanced filtering (date, emotion, topics, risk level)
- 💾 SQLite database with full-text search (FTS5)
- 🚀 React frontend with Tailwind CSS
- 🐳 Docker containerization for easy deployment

## Project Structure

```
vps-question-answer-search/
├── backend/           # Flask backend application
├── frontend/          # React frontend application
├── telegram_bot/      # Telegram bot for user management
├── scripts/           # Data processing and migration scripts
├── data/              # Data directory (JSON files, database)
└── logs/              # Application logs
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- OpenRouter API key
- Telegram Bot Token

### 1. Clone and Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Process Data and Initialize Database

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Extract and normalize data
python scripts/process_data.py

# Translate QA pairs (this will take time and use API credits)
python scripts/translate_qa.py

# Initialize database
python scripts/init_db.py
```

### 3. Start Telegram Bot (for user management)

```bash
cd telegram_bot
pip install -r requirements.txt
python bot.py
```

Use these commands in Telegram:
- `/add_user <username> <password>` - Add new user
- `/list_users` - List all users
- `/remove_user <username>` - Remove user

### 4. Start Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

📖 **For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

## API Endpoints

- `POST /api/auth/login` - User login
- `GET /api/search` - Search QA pairs
- `GET /api/filters` - Get available filters
- `GET /api/conversations` - List conversations
- `GET /api/qa/:id` - Get specific QA pair
- `GET /api/export` - Export search results

## License

MIT
