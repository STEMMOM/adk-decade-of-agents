"""
P12 — First Cross-Process Stateful Agent (SQLite Sessions)

This script demonstrates:
1. Writing Session.events to SQLite
2. Reusing the same session_id across runs
3. Inspecting the underlying ledger
"""

import asyncio
import sqlite3
import os

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

# -------------------------
# 🔧 Global Constants
# -------------------------

MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "agents"
USER_ID = "susan"

# Compute PROJECT_ROOT = adk-decade-of-agents/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "day3_sessions.db")

# Async SQLAlchemy driver + absolute path
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"


# -------------------------
# 🔧 Main Logic
# -------------------------

async def main() -> None:
    print("✅ P12 — stateful_db: starting\n")

    # 1. Create Agent
    agent = LlmAgent(
        model=Gemini(model=MODEL_NAME),
        name="db_agent",
        description="Agent with SQLite-backed persistent sessions.",
    )

    # 2. Session service uses SQLite (persistent)
    session_service = DatabaseSessionService(db_url=DB_URL)

    # 3. Runner
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    session_id = "db-demo-session"

    # 4. Create or reuse persistent session
    try:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        print(f"✅ Created new persistent session: {session_id}")
    except Exception:
        await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        print(f"♻️ Reusing existing persistent session: {session_id}")

    # 5. Send messages
    async def send(query: str):
        print(f"\nUser[{session_id}] > {query}")

        content = types.Content(
            role="user",
            parts=[types.Part(text=query)],
        )

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                print(f"AI[{session_id}]   > {event.content.parts[0].text}")

    await send("Hi, I am Sam! What is the capital of the United States?")
    await send("Hello again! What is my name?")

    # 6. Show session events (via ADK)
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    print("\n--- SESSION EVENTS (from DatabaseSessionService) ---")
    for idx, e in enumerate(session.events):
        content = ""
        if e.content and getattr(e.content, "parts", None):
            content = e.content.parts[0].text
        print(f"- [{idx}] {e.author}: {content}")

    # 7. Raw DB inspection via sqlite3
    print("\n--- RAW DB EVENTS (sqlite3) ---")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT app_name, session_id, author, content
            FROM events
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,),
        )
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to inspect SQLite DB: {e}")

    print("\n✅ P12 — finished.")


if __name__ == "__main__":
    asyncio.run(main())

