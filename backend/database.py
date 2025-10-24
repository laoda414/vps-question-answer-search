"""
Database operations and models
"""

import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import bcrypt

from config import config


class Database:
    """Database connection and operations manager"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH

    @contextmanager
    def get_connection(self, read_only: bool = False):
        """Get database connection with context manager"""
        uri = f"file:{self.db_path}{'?mode=ro' if read_only else ''}"
        conn = sqlite3.connect(uri, uri=True, timeout=10.0)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: Tuple = (), read_only: bool = True) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        with self.get_connection(read_only=read_only) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if read_only:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return []

    def execute_one(self, query: str, params: Tuple = (), read_only: bool = True) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result"""
        with self.get_connection(read_only=read_only) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if read_only:
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                conn.commit()
                return None

    # User Management

    def create_user(self, username: str, password: str, telegram_id: str = None) -> int:
        """Create a new user"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with self.get_connection(read_only=False) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, telegram_id)
                VALUES (?, ?, ?)
            """, (username, password_hash, telegram_id))
            conn.commit()
            return cursor.lastrowid

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return self.execute_one(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        user = self.get_user_by_username(username)
        if not user:
            return False

        return bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))

    def update_last_login(self, username: str):
        """Update user's last login timestamp"""
        self.execute_query(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
            (username,),
            read_only=False
        )

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        return self.execute_query(
            "SELECT id, username, telegram_id, created_at, last_login FROM users"
        )

    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        with self.get_connection(read_only=False) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return cursor.rowcount > 0

    # Search Operations

    def search_qa_pairs(
        self,
        query: str = None,
        date_from: str = None,
        date_to: str = None,
        emotion_tone: str = None,
        conversation_id: int = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search QA pairs with filters
        Returns: (results, total_count)
        """

        # Base query
        if query:
            # Full-text search
            sql = """
                SELECT
                    qa.id, qa.question_pt, qa.question_en,
                    qa.answer_pt, qa.answer_en,
                    qa.context, qa.context_en,
                    qa.date, qa.emotion_tone,
                    c.file_name, c.overall_tone, c.potential_scam,
                    fts.rank
                FROM qa_pairs qa
                JOIN qa_search_fts fts ON qa.id = fts.rowid
                JOIN conversations c ON qa.conversation_id = c.id
                WHERE qa_search_fts MATCH ?
            """
            params = [query]
        else:
            # Browse all
            sql = """
                SELECT
                    qa.id, qa.question_pt, qa.question_en,
                    qa.answer_pt, qa.answer_en,
                    qa.context, qa.context_en,
                    qa.date, qa.emotion_tone,
                    c.file_name, c.overall_tone, c.potential_scam
                FROM qa_pairs qa
                JOIN conversations c ON qa.conversation_id = c.id
                WHERE 1=1
            """
            params = []

        # Add filters
        if date_from:
            sql += " AND qa.date >= ?"
            params.append(date_from)

        if date_to:
            sql += " AND qa.date <= ?"
            params.append(date_to)

        if emotion_tone:
            sql += " AND qa.emotion_tone = ?"
            params.append(emotion_tone)

        if conversation_id:
            sql += " AND qa.conversation_id = ?"
            params.append(conversation_id)

        # Get total count
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as subquery"
        count_result = self.execute_one(count_sql, tuple(params))
        total_count = count_result['total'] if count_result else 0

        # Add ordering and pagination
        if query:
            sql += " ORDER BY fts.rank, qa.date DESC"
        else:
            sql += " ORDER BY qa.date DESC, qa.id DESC"

        offset = (page - 1) * per_page
        sql += f" LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        # Execute search
        results = self.execute_query(sql, tuple(params))

        return results, total_count

    def get_qa_pair_by_id(self, qa_id: int) -> Optional[Dict[str, Any]]:
        """Get single QA pair with full context"""
        return self.execute_one("""
            SELECT
                qa.*,
                c.file_name, c.start_date, c.end_date,
                c.overall_tone, c.potential_scam, c.risk_explanation
            FROM qa_pairs qa
            JOIN conversations c ON qa.conversation_id = c.id
            WHERE qa.id = ?
        """, (qa_id,))

    # Filters and Metadata

    def get_available_emotions(self) -> List[str]:
        """Get list of all emotion tones"""
        results = self.execute_query("""
            SELECT DISTINCT emotion_tone
            FROM qa_pairs
            WHERE emotion_tone IS NOT NULL AND emotion_tone != ''
            ORDER BY emotion_tone
        """)
        return [r['emotion_tone'] for r in results]

    def get_date_range(self) -> Dict[str, str]:
        """Get min and max dates"""
        result = self.execute_one("""
            SELECT MIN(date) as min_date, MAX(date) as max_date
            FROM qa_pairs
            WHERE date IS NOT NULL
        """)
        return result or {'min_date': None, 'max_date': None}

    def get_conversations_list(self) -> List[Dict[str, Any]]:
        """Get list of all conversations"""
        return self.execute_query("""
            SELECT
                c.id, c.file_name, c.start_date, c.end_date,
                c.total_messages, c.overall_tone, c.potential_scam,
                COUNT(qa.id) as qa_count
            FROM conversations c
            LEFT JOIN qa_pairs qa ON c.id = qa.conversation_id
            GROUP BY c.id
            ORDER BY c.start_date DESC
        """)

    def get_topics_by_conversation(self, conversation_id: int) -> List[str]:
        """Get topics for a conversation"""
        results = self.execute_query("""
            SELECT topic_name
            FROM topics
            WHERE conversation_id = ?
            ORDER BY topic_name
        """, (conversation_id,))
        return [r['topic_name'] for r in results]

    # Statistics

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}

        # Total counts
        stats['total_users'] = self.execute_one("SELECT COUNT(*) as count FROM users")['count']
        stats['total_conversations'] = self.execute_one("SELECT COUNT(*) as count FROM conversations")['count']
        stats['total_qa_pairs'] = self.execute_one("SELECT COUNT(*) as count FROM qa_pairs")['count']

        # Date range
        stats['date_range'] = self.get_date_range()

        # Emotion distribution
        emotion_dist = self.execute_query("""
            SELECT emotion_tone, COUNT(*) as count
            FROM qa_pairs
            WHERE emotion_tone != ''
            GROUP BY emotion_tone
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['emotion_distribution'] = emotion_dist

        # Risk assessment
        scam_count = self.execute_one("SELECT COUNT(*) as count FROM conversations WHERE potential_scam = 1")['count']
        stats['potential_scam_count'] = scam_count
        stats['scam_percentage'] = (scam_count / stats['total_conversations'] * 100) if stats['total_conversations'] > 0 else 0

        return stats


# Global database instance
db = Database()
