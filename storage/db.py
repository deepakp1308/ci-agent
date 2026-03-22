"""SQLite storage for weekly snapshots, history, and trend deltas."""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_db_path: Optional[str] = None


def _get_db_path() -> str:
    global _db_path
    if _db_path is None:
        _db_path = os.environ.get("DB_PATH", "./storage/ci_agent.db")
    return _db_path


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS product_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor TEXT NOT NULL,
                week_iso TEXT NOT NULL,
                json_data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sentiment_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor TEXT NOT NULL,
                week_iso TEXT NOT NULL,
                json_data TEXT NOT NULL,
                sentiment_score REAL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS report_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_iso TEXT NOT NULL,
                triggered_by TEXT NOT NULL,
                html_path TEXT,
                pdf_path TEXT,
                slack_thread_ts TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_product_competitor_week
                ON product_snapshots(competitor, week_iso);
            CREATE INDEX IF NOT EXISTS idx_sentiment_competitor_week
                ON sentiment_snapshots(competitor, week_iso);
        """)
        conn.commit()
        logger.info("Database initialized successfully")
    finally:
        conn.close()


def store_product_snapshot(competitor: str, week_iso: str, data_dict: dict):
    """Store a product intelligence snapshot."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO product_snapshots (competitor, week_iso, json_data) VALUES (?, ?, ?)",
            (competitor, week_iso, json.dumps(data_dict, default=str)),
        )
        conn.commit()
        logger.info(f"Stored product snapshot: {competitor} / {week_iso}")
    finally:
        conn.close()


def get_product_history(competitor: str, n_weeks: int = 12) -> list[dict]:
    """Get last n_weeks of product snapshots for a competitor."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT week_iso, json_data, created_at FROM product_snapshots "
            "WHERE competitor = ? ORDER BY week_iso DESC LIMIT ?",
            (competitor, n_weeks),
        ).fetchall()
        results = []
        for row in rows:
            data = json.loads(row["json_data"])
            data["_week_iso"] = row["week_iso"]
            data["_created_at"] = row["created_at"]
            results.append(data)
        return results
    finally:
        conn.close()


def store_sentiment_snapshot(competitor: str, week_iso: str, data_dict: dict):
    """Store a sentiment analysis snapshot."""
    score = data_dict.get("sentiment_score", 0.0)
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO sentiment_snapshots (competitor, week_iso, json_data, sentiment_score) "
            "VALUES (?, ?, ?, ?)",
            (competitor, week_iso, json.dumps(data_dict, default=str), score),
        )
        conn.commit()
        logger.info(f"Stored sentiment snapshot: {competitor} / {week_iso} (score={score})")
    finally:
        conn.close()


def get_sentiment_history(competitor: str, n_weeks: int = 12) -> list[dict]:
    """Get last n_weeks of sentiment snapshots for a competitor."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT week_iso, json_data, sentiment_score, created_at FROM sentiment_snapshots "
            "WHERE competitor = ? ORDER BY week_iso DESC LIMIT ?",
            (competitor, n_weeks),
        ).fetchall()
        results = []
        for row in rows:
            data = json.loads(row["json_data"])
            data["_week_iso"] = row["week_iso"]
            data["_sentiment_score"] = row["sentiment_score"]
            data["_created_at"] = row["created_at"]
            results.append(data)
        return results
    finally:
        conn.close()


def log_report_run(
    week_iso: str,
    triggered_by: str,
    html_path: str = "",
    pdf_path: str = "",
    slack_thread_ts: str = "",
):
    """Log a report generation run."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO report_runs (week_iso, triggered_by, html_path, pdf_path, slack_thread_ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (week_iso, triggered_by, html_path, pdf_path, slack_thread_ts),
        )
        conn.commit()
        logger.info(f"Logged report run: {week_iso} / {triggered_by}")
    finally:
        conn.close()


def get_last_run() -> Optional[dict]:
    """Get the most recent report run."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM report_runs ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def get_recent_runs(n: int = 4) -> list[dict]:
    """Get the last n report runs."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM report_runs ORDER BY created_at DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
