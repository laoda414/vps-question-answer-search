#!/bin/bash
# Install all dependencies for the QA Search project

set -e  # Exit on error

echo "=================================================="
echo "Installing QA Search Interface Dependencies"
echo "=================================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create it first with: python3 -m venv venv"
    exit 1
fi

# Activate venv
echo "✅ Using virtual environment: venv"
PIP="./venv/bin/pip"
PYTHON="./venv/bin/python"

# Upgrade pip
echo ""
echo "Upgrading pip..."
$PIP install --upgrade pip

# Install all dependencies
echo ""
echo "📦 Installing backend dependencies..."
$PIP install -r backend/requirements.txt

echo ""
echo "📦 Installing script dependencies..."
$PIP install -r scripts/requirements.txt

echo ""
echo "📦 Installing telegram bot dependencies..."
$PIP install -r telegram_bot/requirements.txt

# Verify installation
echo ""
echo "=================================================="
echo "Verifying Installation"
echo "=================================================="
echo ""

echo "Python packages installed:"
$PIP list | grep -E "Flask|telegram|bcrypt|aiohttp|requests|tqdm|dotenv"

echo ""
echo "=================================================="
echo "✅ All dependencies installed successfully!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Configure .env file with your API keys"
echo "2. Process data: python scripts/process_data.py"
echo "3. Translate: python scripts/translate_qa_parallel.py"
echo "4. Initialize DB: python scripts/init_db.py"
echo "5. Start services (in separate terminals):"
echo "   - Telegram bot: python telegram_bot/bot.py"
echo "   - Backend: python backend/app.py"
echo "   - Frontend: cd frontend && npm install && npm run dev"
echo ""
