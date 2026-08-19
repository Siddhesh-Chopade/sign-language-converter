"""
db.py
-----
Small helper module for talking to MySQL. Keeps the SQL in one place
so app.py stays focused on the API/routing logic.
"""

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",   # change this
    "database": "sign_language_db",
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def insert_sign(sign_text, confidence):
    """Save a confirmed sign recognition to the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO recognized_signs (sign_text, confidence) VALUES (%s, %s)",
            (sign_text, confidence)
        )
        conn.commit()
    except Error as e:
        print(f"[db] Could not insert sign: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_recent_signs(limit=15):
    """Fetch the most recent recognized signs, newest first."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT sign_text, confidence, created_at "
            "FROM recognized_signs ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print(f"[db] Could not fetch history: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
