"""
storage.py
----------
Local SQLite storage for persisting ResearchStack sessions.
"""

import sqlite3
import json
import os
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "research_history.db")


def init_db():
    """Create the research reports table if it doesn't already exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            topic TEXT NOT NULL,
            score INTEGER,
            revisions INTEGER,
            report TEXT NOT NULL,
            feedback TEXT,
            search_results TEXT,
            scraped_content TEXT,
            history_json TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_report(
    topic: str,
    score: int,
    revisions: int,
    report: str,
    feedback: str,
    search_results: str,
    scraped_content: str,
    history: List[dict]
) -> int:
    """Save a finished research run to SQLite and return the row ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports (
            topic, score, revisions, report, feedback, search_results, scraped_content, history_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        topic,
        score,
        revisions,
        report,
        feedback,
        search_results,
        scraped_content,
        json.dumps(history)
    ))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def list_reports(limit: int = 30) -> List[Dict]:
    """Retrieve saved reports list ordered by most recent."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, topic, score, revisions
        FROM reports
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_report_by_id(report_id: int) -> Optional[Dict]:
    """Fetch full report content by ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        try:
            data["history"] = json.loads(data["history_json"])
        except Exception:
            data["history"] = []
        return data
    return None


def delete_report(report_id: int):
    """Delete a report by ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()

