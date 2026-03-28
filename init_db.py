#!/usr/bin/env python3
"""
Database initialization script for SQLite injection CTF challenge.
This script creates:
1. Main database (app.db) with a 'secrets' table containing hints and the flag.
The flag is pulled from the FLAG environment variable.
"""

import sqlite3
import os
import sys

def init_database():
    """Initialize the main application database with secrets table."""
    db_path = "/app/data/app.db"
    
    flag = os.environ.get("FLAG_1", "FLAG_1_NOT_SET")
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create secrets table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value TEXT NOT NULL
        )
    """)
    
    # Check if secrets already exist
    cursor.execute("SELECT COUNT(*) FROM secrets")
    count = cursor.fetchone()[0]
    
    if count == 0:
        secrets_data = [
            ("real_flag", flag)
        ]
        
        cursor.executemany("INSERT INTO secrets (name, value) VALUES (?, ?)", secrets_data)
        print("✓ Secrets table created and populated")
    else:
        print("✓ Secrets table already exists")
    
    conn.commit()
    conn.close()


def main():
    """Run all database initialization functions."""
    
    print("\n[1] Initializing main database...")
    init_database()

if __name__ == "__main__":
    main()
