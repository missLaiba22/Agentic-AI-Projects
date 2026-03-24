import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from langgraph.checkpoint.sqlite import SqliteSaver

# Database path
DB_PATH = Path(__file__).parent.parent / "verdara.db"


def get_db_connection() -> sqlite3.Connection:
    """Create a SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    
    # Audit log table (human interactions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            action TEXT NOT NULL,
            original_verdict TEXT,
            edited_verdict TEXT,
            edit_summary TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_session_ts
        ON audit_log (session_id, timestamp)
        """
    )
    
    conn.commit()
    conn.close()

def get_checkpointer():
    """Get SqliteSaver checkpointer for LangGraph."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return SqliteSaver(conn)

def create_session(session_id: str, question: str) -> None:
    """Create a new session entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (session_id, question, status, start_time)
        VALUES (?, ?, 'created', ?)
    """, (session_id, question, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT session_id, question, start_time, end_time, status
        FROM sessions WHERE session_id = ?
    """, (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "session_id": row["session_id"],
            "question": row["question"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "status": row["status"],
        }
    return None

def list_sessions(limit: int = 20, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all sessions, optionally filtered by status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute("""
            SELECT session_id, question, start_time, end_time, status
            FROM sessions WHERE status = ? ORDER BY created_at DESC LIMIT ?
        """, (status, limit))
    else:
        cursor.execute("""
            SELECT session_id, question, start_time, end_time, status
            FROM sessions ORDER BY created_at DESC LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "session_id": row["session_id"],
            "question": row["question"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "status": row["status"],
        }
        for row in rows
    ]

def log_human_decision(
    session_id: str, 
    action: str, 
    original_verdict: Optional[str] = None,
    edited_verdict: Optional[str] = None,
    edit_summary: Optional[str] = None
) -> None:
    """Log human interaction to audit trail."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log (session_id, action, original_verdict, edited_verdict, edit_summary)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, action, original_verdict, edited_verdict, edit_summary))
    conn.commit()
    conn.close()

def update_session_status(session_id: str, status: str, end_time: Optional[str] = None) -> None:
    """Update session status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    terminal_statuses = {"completed", "failed", "cancelled"}
    if status in terminal_statuses:
        final_time = end_time or datetime.now().isoformat()
        cursor.execute(
            """
            UPDATE sessions SET status = ?, end_time = ? WHERE session_id = ?
            """,
            (status, final_time, session_id),
        )
    else:
        cursor.execute(
            """
            UPDATE sessions SET status = ?, end_time = NULL WHERE session_id = ?
            """,
            (status, session_id),
        )
    conn.commit()
    conn.close()

def get_audit_log(session_id: str) -> List[Dict[str, Any]]:
    """Get all human interactions for a session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action, original_verdict, edited_verdict, edit_summary, timestamp
        FROM audit_log WHERE session_id = ? ORDER BY timestamp
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "action": row["action"],
            "original_verdict": row["original_verdict"],
            "edited_verdict": row["edited_verdict"],
            "edit_summary": row["edit_summary"],
            "timestamp": row["timestamp"],
        }
        for row in rows
    ]