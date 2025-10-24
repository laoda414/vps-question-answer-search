"""
Database Initialization Script
Creates SQLite database schema and populates with translated QA pairs
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "translated_qa_pairs.json"
DB_PATH = PROJECT_ROOT / "data" / "qa_search.db"


def create_schema(conn: sqlite3.Connection):
    """Create database schema"""
    cursor = conn.cursor()

    print("Creating database schema...")

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            telegram_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT UNIQUE NOT NULL,
            start_date DATE,
            end_date DATE,
            total_messages INTEGER,
            conversation_duration TEXT,
            overall_tone TEXT,
            potential_scam BOOLEAN,
            risk_explanation TEXT
        )
    """)

    # QA pairs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            question_pt TEXT NOT NULL,
            question_en TEXT,
            answer_pt TEXT NOT NULL,
            answer_en TEXT,
            context TEXT,
            context_en TEXT,
            date DATE,
            emotion_tone TEXT,
            source TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    # Topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            topic_name TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_date ON qa_pairs(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_emotion ON qa_pairs(emotion_tone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_conversation ON qa_pairs(conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_date ON conversations(start_date, end_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_conversation ON topics(conversation_id)")

    # Create FTS5 virtual table for full-text search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS qa_search_fts USING fts5(
            question_pt,
            question_en,
            answer_pt,
            answer_en,
            context,
            context_en,
            content='qa_pairs',
            content_rowid='id'
        )
    """)

    # Create triggers to keep FTS index in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS qa_pairs_ai AFTER INSERT ON qa_pairs BEGIN
            INSERT INTO qa_search_fts(rowid, question_pt, question_en, answer_pt, answer_en, context, context_en)
            VALUES (new.id, new.question_pt, new.question_en, new.answer_pt, new.answer_en, new.context, new.context_en);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS qa_pairs_ad AFTER DELETE ON qa_pairs BEGIN
            DELETE FROM qa_search_fts WHERE rowid = old.id;
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS qa_pairs_au AFTER UPDATE ON qa_pairs BEGIN
            UPDATE qa_search_fts
            SET question_pt = new.question_pt,
                question_en = new.question_en,
                answer_pt = new.answer_pt,
                answer_en = new.answer_en,
                context = new.context,
                context_en = new.context_en
            WHERE rowid = new.id;
        END
    """)

    conn.commit()
    print("✅ Schema created successfully")


def insert_conversation(cursor: sqlite3.Cursor, conv_info: Dict[str, Any]) -> int:
    """Insert or get conversation ID"""

    # Check if conversation exists
    cursor.execute("SELECT id FROM conversations WHERE file_name = ?", (conv_info['file_name'],))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Insert new conversation
    cursor.execute("""
        INSERT INTO conversations (
            file_name, start_date, end_date, total_messages,
            conversation_duration, overall_tone, potential_scam, risk_explanation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        conv_info['file_name'],
        conv_info.get('start_date'),
        conv_info.get('end_date'),
        conv_info.get('total_messages'),
        conv_info.get('conversation_duration'),
        conv_info.get('overall_tone'),
        conv_info.get('potential_scam'),
        conv_info.get('risk_explanation')
    ))

    conversation_id = cursor.lastrowid

    # Insert topics
    topics = conv_info.get('topics', [])
    for topic in topics:
        cursor.execute("""
            INSERT INTO topics (conversation_id, topic_name) VALUES (?, ?)
        """, (conversation_id, topic))

    return conversation_id


def populate_database(conn: sqlite3.Connection, qa_pairs: List[Dict[str, Any]]):
    """Populate database with QA pairs"""
    cursor = conn.cursor()

    print(f"Populating database with {len(qa_pairs)} QA pairs...")

    # Track unique conversations
    conversation_map = {}
    skipped_count = 0

    for idx, qa in enumerate(qa_pairs, 1):
        if idx % 100 == 0:
            print(f"  Processed {idx}/{len(qa_pairs)} QA pairs...")

        # Skip QA pairs with missing required fields
        if not qa.get('question_pt') or not qa.get('answer_pt'):
            skipped_count += 1
            continue

        # Get or create conversation
        file_name = qa['conversation']['file_name']
        if file_name not in conversation_map:
            conversation_id = insert_conversation(cursor, qa['conversation'])
            conversation_map[file_name] = conversation_id
        else:
            conversation_id = conversation_map[file_name]

        # Insert QA pair with defaults for missing fields
        cursor.execute("""
            INSERT INTO qa_pairs (
                conversation_id, question_pt, question_en, answer_pt, answer_en,
                context, context_en, date, emotion_tone, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conversation_id,
            qa.get('question_pt', ''),
            qa.get('question_en', ''),
            qa.get('answer_pt', ''),
            qa.get('answer_en', ''),
            qa.get('context', ''),
            qa.get('context_en', ''),
            qa.get('date'),
            qa.get('emotion_tone', ''),
            qa.get('source', '')
        ))

    conn.commit()

    if skipped_count > 0:
        print(f"⚠️  Skipped {skipped_count} QA pairs with missing required fields")
    print(f"✅ Database populated successfully with {len(qa_pairs) - skipped_count} QA pairs")


def enable_wal_mode(conn: sqlite3.Connection):
    """Enable WAL mode for better concurrency"""
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    result = cursor.fetchone()
    journal_mode = result[0] if result else "unknown"
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    print(f"✅ WAL mode enabled: {journal_mode}")


def print_statistics(conn: sqlite3.Connection):
    """Print database statistics"""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("Database Statistics")
    print("=" * 60)

    # Count conversations
    cursor.execute("SELECT COUNT(*) FROM conversations")
    conv_count = cursor.fetchone()[0]
    print(f"Total conversations: {conv_count}")

    # Count QA pairs
    cursor.execute("SELECT COUNT(*) FROM qa_pairs")
    qa_count = cursor.fetchone()[0]
    print(f"Total QA pairs: {qa_count}")

    # Count topics
    cursor.execute("SELECT COUNT(*) FROM topics")
    topic_count = cursor.fetchone()[0]
    print(f"Total topics: {topic_count}")

    # Date range
    cursor.execute("SELECT MIN(date), MAX(date) FROM qa_pairs WHERE date IS NOT NULL")
    date_range = cursor.fetchone()
    print(f"Date range: {date_range[0]} to {date_range[1]}")

    # Emotion distribution
    cursor.execute("""
        SELECT emotion_tone, COUNT(*)
        FROM qa_pairs
        WHERE emotion_tone != ''
        GROUP BY emotion_tone
        ORDER BY COUNT(*) DESC
    """)
    emotions = cursor.fetchall()
    print("\nEmotion distribution:")
    for emotion, count in emotions[:5]:
        print(f"  {emotion}: {count}")

    # Risk assessment
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE potential_scam = 1")
    scam_count = cursor.fetchone()[0]
    print(f"\nPotential scam conversations: {scam_count} ({scam_count/conv_count*100:.1f}%)")


def main():
    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)
    print()

    # Check for input file
    if not INPUT_FILE.exists():
        print(f"❌ Error: Input file not found: {INPUT_FILE}")
        print("Please run 'python scripts/translate_qa.py' first")
        return

    # Load translated data
    print(f"Loading data from: {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    qa_pairs = data['qa_pairs']
    print(f"Loaded {len(qa_pairs)} QA pairs\n")

    # Create database directory
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Check if database exists
    if DB_PATH.exists():
        print(f"⚠️  Database already exists at: {DB_PATH}")
        print("Do you want to recreate it? This will delete all existing data. (y/n): ", end='')
        response = input().strip().lower()
        if response != 'y':
            print("Database initialization cancelled.")
            return
        DB_PATH.unlink()

    # Connect to database
    print(f"Creating database at: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))

    try:
        # Create schema
        create_schema(conn)

        # Enable WAL mode for concurrency
        enable_wal_mode(conn)

        # Populate database
        populate_database(conn, qa_pairs)

        # Print statistics
        print_statistics(conn)

        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print(f"\nDatabase location: {DB_PATH}")
        print(f"Database size: {DB_PATH.stat().st_size / 1024 / 1024:.2f} MB")
        print("\nNext steps:")
        print("1. Start the Telegram bot: python telegram_bot/bot.py")
        print("2. Add users via Telegram bot")
        print("3. Start the backend: python backend/app.py")
        print("4. Start the frontend: cd frontend && npm start")

    except Exception as e:
        print(f"\n❌ Error during database initialization: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
