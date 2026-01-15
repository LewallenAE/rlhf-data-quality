#!/usr/bin/env python3
"""
Database layer for RLHF Data Quality System

Provides schema definitions, connection management, and query interfaces.
"""

# -------------- Futures -------------

from __future__ import annotations

# -------------- Standard Library ---------

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# ------------- Third Party Library ---------------
# N/A for now

# -------------- Application Imports --------------

from settings import get_config

# -------------- Module-level Configuration -------

config = get_config()
logger = logging.getLogger(__name__)

# -------------- Constants ------------------------

CURRENT_SCHEMA_VERSION = 1

# -------------- Schema Definiton ------------------

"""
SCHEMA for SQlite database

This creates a table if it does not exist and skips if it does exist

pair_id TEXT PRIMARY KEY -- a unique id you provide such as "hh-rlhf-00001"
chosen TEXT NOT NULL -- The preferred response this must have a value
rejected TEXT NOT NULL -- The rejected response this must have a value
source_dataset TEXT NOT NULL -- Where this information came from such as "hh-rlhf"
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Auto-fills with the current time
"""
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS response_pairs (
    pair_id TEXT PRIMARY KEY,
    chosen TEXT NOT NULL,
    rejected TEXT NOT NULL,
    source_dataset TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detections (
    detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    severity REAL NOT NULL CHECK (severity >= 0.0 AND severity <= 1.0),
    metadata TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pair_id) REFERENCES response_pairs(pair_id)
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_detections_pair_id ON detections(pair_id);
CREATE INDEX IF NOT EXISTS idx_detections_signal_type ON detections(signal_type);
CREATE INDEX IF NOT EXISTS idx_detections_severity ON detections(severity);
"""

# ---------------- Connection Management -----------------------

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    
    Automatically commits on success, rolls back on error, and always closes.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM detections")

    Yield:
        sqlite3.Connection withy Row factory enabled
    """
    conn = sqlite3.connect(config.db_path)
    conn.row_factory = sqlite3.Row # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON") # Enforce foreign key constraints
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ---------------------- Schema Management -------------------

def init_db() -> None:
    """
    Initialize database with schema.

    Creates tables, indexes, and sets schema version if not already set.
    Safe to call muiltiple times (idempotent).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Execute schema
        cursor.executescript(SCHEMA_SQL)

        # Set schema version if not set
        cursor.execute("SELECT version FROM schema_version WHERE version = ?", (CURRENT_SCHEMA_VERSION,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (CURRENT_SCHEMA_VERSION,))
            logger.info(f"Initialized database with schema version {CURRENT_SCHEMA_VERSION}")
        else:
            logger.info(f"Database already at schema version {CURRENT_SCHEMA_VERSION}")

def get_schema_version() -> int | None:
    """
    Get current database schema version.

    Returns:
        Current schema version or None if not initialized.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_version")
            row = cursor.fetchone()
            return row[0] if row else None
    except sqlite3.OperationalError:
        # Table doesn't yet exist
        return None
    

# ------------------- Response Pair Operations --------------------

def insert_response_pair(
        pair_id: str,
        chosen: str,
        rejected: str,
        source_dataset: str
) -> None:
    """ Insert a response pair into the database.
    
    Args:
        pair_id: Unique Identifier for the pair
        chosen: The preferred response
        rejected: The rejected response
        source_dataset: Source data set name (e.g. "hh-rlhf")

    Raise:
        sqlite3.IntegrityError: If pair_id already exists
    """

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO response_pairs (pair_id, chosen, rejected, source_dataset)
            VALUES (?, ?, ?, ?)
            """,
            (pair_id, chosen, rejected, source_dataset)
        )
        logger.debug(f"Inserted response pair: {pair_id}")



def get_response_pair(pair_id: str) -> sqlite3.Row | None:
    """
    Retriever a response pair by id
    
    Args:
        pair_id: Unique identified for the pair
    
    Returns:
        Row object with columns: pair_id, chosen, rejected, source_dataset, created_at
        None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM response_pairs WHERE pair_id = ?",
            (pair_id,)
        )
        return cursor.fetchone()

def get_all_pair_ids() -> list[str]:
    """
    Get all response pair IDs.

    Returns:
        list of pair IDs
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT pair_id FROM response_pairs ORDER by created_at")
        return [row[0] for row in cursor.fetchall()]
    
def count_response_pairs() -> int:
    """
    Count total response pairs in database.

    Returns:
        Number of response pairs
    """
    with get_db_connection() as conn:
        cursor =conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM response_pairs")
        return cursor.fetchone()[0]
    
# ------------------- Detection Operations --------------------

def insert_detection(
        pair_id: str,
        signal_type: str,
        severity: float,
        metadata: dict | None = None
) -> int:
    """
    Insert a detection result
    
    Args:
    :param pair_id: ID of the response pair with the issue
    :type pair_id: str
    :param signal_type: Type of detection signal (e.g. "semantic duplicate")
    :type signal_type: str
    :param severity: Severity score between 0.0 and 1.0
    :type severity: float
    :param metadata: Optional dict with signal-specific details (serialized to JSON)
    :type metadata: dict | None

    Returns:
        Returns the detection id in question
    :rtype: int

    Raises:
        sqlite3.IntegrityError: If paid_id doesn't exist (foregin key violation)
        ValueError: If severity not in [0.0, 1.0]
    """
    if not 0.0 <= severity <= 1.0:
        raise ValueError(f"Severity must be between 0.0 and 1.0, got {severity}")
    
    metadata_json = json.dumps(metadata) if metadata else None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO detections (pair_id, signal_type, severity, metadata)
            VALUES (?, ?, ?, ?)
            """,
            (pair_id, signal_type, severity, metadata_json)
        )
        detection_id = cursor.lastrowid
        logger.debug(f"Inserted detection {detection_id}: {signal_type} for {pair_id}")
        return detection_id
    
def get_detections_for_pair(pair_id: str) -> list[sqlite3.Row]:
    """
    Get all detections for a specific response pair.

    Args: 
        pair_id: Response pair ID

    Returns:
        List of detection rows:
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM detections
            WHERE pair_id = ?
            ORDER BY severity DESC, detected_at
            """,
            (pair_id,)
        ) 
        return cursor.fetchall()
    
def get_detections_by_signal(signal_type: str, min_severity:float = 0.0) -> list[sqlite3.Row]:
    """
   Get all detections for specific signal type.
    
    Args:
        signal_type: Type of detection signal
        min_severity: Minimum severity threshold (default: 0.0)
    
    Returns:
        List of detection rows sorted by severity (highest first)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM detections
            WHERE signal_type = ? AND severity >= ?
            ORDER BY severity DESC, detected_at
            """,
            (signal_type, min_severity)
        )
        return cursor.fetchall()

def get_high_severity_detections(min_severity: float = 0.9) -> list[sqlite3.Row]:
    """
    Get all high-severity detections across all signal types.

    Args:
        min_severity: Minimum severity threshold (default: 0.9)
    
    Returns:
        List of detection rows sorted by severity
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT d.*, rp.chosen, rp.rejected
            FROM detections d
            JOIN response_pairs rp ON d.pair_id = rp.pair_id
            WHERE d.severity >= ?
            ORDER BY d.severity DESC, d.detected_at
        """,
        (min_severity,)        
        )
        return cursor.fetchall()
    
def count_detections_by_signal() -> dict[str, int]:
    """
    Count detections grouped by signal type.
    
    Returns:
        Dict mapping signal_type to count
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT signal_type, COUNT(*) as count
            FROM detections
            GROUP BY signal_type
            ORDER BY count DESC
        """
        )
        return {row["signal_type"]: row["count"] for row in cursor.fetchall()}
    
def get_detection_statistics() -> dict:
    """
   Get summary of statistics about detections.
    
    Returns:
        Dict with statistics: total_detections, by_signal, avg_severity, etc.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM detections"
        )
        total = cursor.fetchone()[0]

        # By signal type
        cursor.execute(
            """
            SELECT signal_type, COUNT(*) as count, AVG(severity) as avg_severity
            FROM detections
            GROUP by signal_type
            """
        )
        by_signal ={
            row["signal_type"]: {
                "count": row["count"],
                "avg_severity": round(row["avg_severity"], 3)
            }
            for row in cursor.fetchall()
        }

        # Severity distribution
        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN severity >= 0.9 THEN 1 END) as critical,
                COUNT(CASE WHEN severity >= 0.7 AND severity < 0.9 THEN 1 END) as high,
                COUNT(CASE WHEN severity >= 0.5 AND severity < 0.7 THEN 1 END) as medium,
                COUNT(CASE WHEN severity < 0.5 THEN 1 END) as low
            FROM detections
            """
        )
        severity_dist = dict(cursor.fetchone())

        return {
            "total_detections": total,
            "by_signal": by_signal,
            "severity_distribution": severity_dist
        }
    
# --------------------- Utility Functioins ----------------------

def clear_all_data() -> None:
    """
    DELETE all data from database (keeps schema).

    WARNING: This is desctructive and cannot be undone.
    Use only for testing or reset scenarios.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detections")
        cursor.execute("DELETE FROM response_pairs")
        logger.warning("Cleared all data from database")

def vacuum_db() -> None:
    """
    Optimize database by reclaiming unused space.

    Run periodically after large deletions to reduce file size.
    """
    with get_db_connection() as conn:
        conn.execute("VACUUM")
        logger.info("Database vacuumed successfully")
