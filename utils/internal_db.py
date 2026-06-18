import sqlite3
import os

INTERNAL_DB_FILE = "admin_internal.db"

def get_connection():
    # SQLite will automatically create the file if it doesn't exist
    conn = sqlite3.connect(INTERNAL_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_internal_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS license_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            client_name TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            max_users INTEGER NOT NULL,
            expiry_date TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_license_generation(client_id, client_name, plan_name, max_users, expiry_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO license_history (client_id, client_name, plan_name, max_users, expiry_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (client_id, client_name, plan_name, max_users, expiry_date))
    conn.commit()
    conn.close()

def get_license_history():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM license_history ORDER BY generated_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
