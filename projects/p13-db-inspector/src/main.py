"""
P13 — DB Inspector (Event Ledger Microscope)

Reads the SQLite ledger created by P12 and prints all events.
"""

import sqlite3
import json
import os

# Compute PROJECT_ROOT = adk-decade-of-agents/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "day3_sessions.db")


def pretty_print_event(row):
    app, session_id, author, content_json, timestamp = row

    try:
        content = json.loads(content_json)
        text = content["parts"][0].get("text", "")
    except Exception:
        text = content_json

    print("────────────────────────────────────────────")
    print(f"Session : {session_id}")
    print(f"Author  : {author}")
    print(f"Time    : {timestamp}")
    print(f"Text    : {text}")


def main():
    print("📘 P13 — DB Inspector running...")
    print(f"Looking for DB at: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("❌ ERROR: day3_sessions.db not found.")
        print("   Please run P12 first.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT app_name, session_id, author, content, timestamp
            FROM events
            ORDER BY timestamp ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

    except Exception as e:
        print(f"❌ Failed to read database: {e}")
        return

    if not rows:
        print("⚠️ Database exists but has no events.")
        return

    print(f"\n📦 Found {len(rows)} events:\n")

    for row in rows:
        pretty_print_event(row)

    print("\n🔍 DB Inspector finished.\n")


if __name__ == "__main__":
    main()
