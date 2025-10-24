"""
Telegram Bot for User Management
Only responds to admin Telegram user ID
"""

import os
import sys
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
import bcrypt

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_USER_ID = int(os.getenv("ADMIN_TELEGRAM_USER_ID", "0"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "../data/qa_search.db")

# Validate configuration
if not TELEGRAM_BOT_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file")
    sys.exit(1)

if ADMIN_TELEGRAM_USER_ID == 0:
    print("❌ Error: ADMIN_TELEGRAM_USER_ID not set in .env file")
    sys.exit(1)

# Make path absolute - use DATABASE_PATH from env or default
DB_PATH = Path(DATABASE_PATH) if DATABASE_PATH else Path(__file__).parent.parent / "data" / "qa_search.db"


def get_db_connection():
    """Get database connection"""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at: {DB_PATH}")
    return sqlite3.connect(str(DB_PATH))


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id == ADMIN_TELEGRAM_USER_ID


async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Decorator to restrict commands to admin only"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to the administrator only."
        )
        return False
    return True


# ============================================================================
# Bot Commands
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text(
            "⛔ Access denied. This bot is restricted to the administrator only."
        )
        return

    welcome_message = """
🤖 **QA Search User Management Bot**

Welcome! You can use the following commands to manage users:

**User Management:**
• `/add_user <username> <password>` - Add new user
• `/list_users` - List all users
• `/remove_user <username>` - Remove user
• `/reset_password <username> <new_password>` - Reset user password

**System:**
• `/stats` - Show system statistics
• `/help` - Show this help message

Example:
`/add_user john SecurePass123`
    """

    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    if not await admin_only(update, context):
        return

    await start_command(update, context)


async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new user"""
    if not await admin_only(update, context):
        return

    # Parse arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/add_user <username> <password>`\n\n"
            "Example: `/add_user john SecurePass123`",
            parse_mode='Markdown'
        )
        return

    username = context.args[0]
    password = ' '.join(context.args[1:])  # Allow spaces in password

    # Validate input
    if len(username) < 3:
        await update.message.reply_text("❌ Username must be at least 3 characters long")
        return

    if len(password) < 6:
        await update.message.reply_text("❌ Password must be at least 6 characters long")
        return

    # Add user to database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            await update.message.reply_text(f"❌ User '{username}' already exists")
            conn.close()
            return

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert user
        cursor.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        """, (username, password_hash))

        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"✅ User created successfully!\n\n"
            f"**Username:** `{username}`\n"
            f"**Password:** `{password}`\n\n"
            f"⚠️ Please save these credentials securely and delete this message.",
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error creating user: {str(e)}")


async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users"""
    if not await admin_only(update, context):
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        """)

        users = cursor.fetchall()
        conn.close()

        if not users:
            await update.message.reply_text("No users found in the system.")
            return

        message = "**👥 User List**\n\n"
        for user_id, username, created_at, last_login in users:
            last_login_str = last_login if last_login else "Never"
            message += f"• **{username}** (ID: {user_id})\n"
            message += f"  Created: {created_at}\n"
            message += f"  Last login: {last_login_str}\n\n"

        message += f"**Total users:** {len(users)}"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Error listing users: {str(e)}")


async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove user"""
    if not await admin_only(update, context):
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Usage: `/remove_user <username>`\n\n"
            "Example: `/remove_user john`",
            parse_mode='Markdown'
        )
        return

    username = context.args[0]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            await update.message.reply_text(f"❌ User '{username}' not found")
            conn.close()
            return

        # Delete user
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ User '{username}' has been removed successfully")

    except Exception as e:
        await update.message.reply_text(f"❌ Error removing user: {str(e)}")


async def reset_password_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user password"""
    if not await admin_only(update, context):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/reset_password <username> <new_password>`\n\n"
            "Example: `/reset_password john NewPass456`",
            parse_mode='Markdown'
        )
        return

    username = context.args[0]
    new_password = ' '.join(context.args[1:])

    if len(new_password) < 6:
        await update.message.reply_text("❌ Password must be at least 6 characters long")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            await update.message.reply_text(f"❌ User '{username}' not found")
            conn.close()
            return

        # Hash new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Update password
        cursor.execute("""
            UPDATE users SET password_hash = ? WHERE username = ?
        """, (password_hash, username))

        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"✅ Password reset successfully!\n\n"
            f"**Username:** `{username}`\n"
            f"**New password:** `{new_password}`\n\n"
            f"⚠️ Please save these credentials securely and delete this message.",
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error resetting password: {str(e)}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system statistics"""
    if not await admin_only(update, context):
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM qa_pairs")
        qa_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM conversations WHERE potential_scam = 1")
        scam_count = cursor.fetchone()[0]

        # Get date range
        cursor.execute("SELECT MIN(date), MAX(date) FROM qa_pairs WHERE date IS NOT NULL")
        date_range = cursor.fetchone()

        conn.close()

        message = "**📊 System Statistics**\n\n"
        message += f"**Users:** {user_count}\n"
        message += f"**Conversations:** {conv_count}\n"
        message += f"**QA Pairs:** {qa_count:,}\n"
        message += f"**Potential Scams:** {scam_count} ({scam_count/conv_count*100:.1f}%)\n\n"

        if date_range[0] and date_range[1]:
            message += f"**Date Range:**\n"
            message += f"From: {date_range[0]}\n"
            message += f"To: {date_range[1]}"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Error retrieving statistics: {str(e)}")


# ============================================================================
# Main
# ============================================================================

def main():
    """Start the bot"""
    print("=" * 60)
    print("QA Search User Management Bot")
    print("=" * 60)
    print(f"Admin User ID: {ADMIN_TELEGRAM_USER_ID}")
    print(f"Database: {DB_PATH}")
    print("=" * 60)
    print("Bot is starting...")

    # Check database exists
    if not DB_PATH.exists():
        print(f"❌ Error: Database not found at {DB_PATH}")
        print("Please run 'python scripts/init_db.py' first")
        sys.exit(1)

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_user", add_user_command))
    application.add_handler(CommandHandler("list_users", list_users_command))
    application.add_handler(CommandHandler("remove_user", remove_user_command))
    application.add_handler(CommandHandler("reset_password", reset_password_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Start bot
    print("✅ Bot started successfully!")
    print("Send /start in Telegram to begin")
    print("Press Ctrl+C to stop")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
