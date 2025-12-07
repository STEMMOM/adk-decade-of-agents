# sessions_day3/stateful_db.py
"""
持久 Session Demo（SQLite 版）

对比 stateful_inmemory.py，这个脚本做了三件事：
1. 使用 DatabaseSessionService，把对话写入 SQLite 数据库 day3_sessions.db
2. 用同一个 session_id 连续对话，证明 Session 机制保持上下文
3. 在脚本末尾用 sqlite3 直接读 events 表，验证数据确实持久化到了磁盘
"""

import asyncio
import sqlite3
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

# Constants
MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "agents"  # 与 ADK 默认 app_name 对齐，避免 mismatch 提示
USER_ID = "susan"
DB_URL = "sqlite:///day3_sessions.db"  # 本地 SQLite 文件


async def main() -> None:
    print("✅ stateful_db.py: main() 开始执行")

    # 1. 创建 LLM Agent（与 inmemory 版本相同）
    agent = LlmAgent(
        model=Gemini(model=MODEL_NAME),
        name="db_agent",
        description="Agent using DatabaseSessionService (SQLite persistent sessions).",
    )

    # 2. 使用 DatabaseSessionService：会话写入 SQLite 文件
    session_service = DatabaseSessionService(db_url=DB_URL)

    # 3. 创建 Runner
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # 4. 准备 Session ID（持久会话的 key）
    session_id = "db-demo-session"

    # 5. 创建 / 获取 Session（首次新建，之后复用）
    try:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        print(f"✅ 新建持久 Session: {session_id}")
    except Exception:
        await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        print(f"♻️ 复用已有持久 Session: {session_id}")

    # 6. 定义两条用户消息
    msg1 = "Hi, I am Sam! What is the capital of the United States?"
    msg2 = "Hello again! What is my name?"

    async def send_one(query: str) -> None:
        print(f"\nUser > {query}")
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
                text = event.content.parts[0].text
                if text and text != "None":
                    print(f"{MODEL_NAME} > {text}")

    # 7. 在同一个 Session 里发送两轮对话
    await send_one(msg1)
    await send_one(msg2)

    # 8. 从 SessionService 视角看事件（与 inmemory 版本类似）
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    print("\n--- SESSION EVENTS (from DatabaseSessionService) ---")
    for e in session.events:
        print(e)

    print("\n--- SESSION STATE ---")
    print(session.state)

    # 9. 直接用 sqlite3 查看底层 events 表，证明已经写入磁盘
    print("\n--- RAW DB EVENTS (sqlite3) ---")
    try:
        conn = sqlite3.connect("day3_sessions.db")
        cursor = conn.cursor()
        # 只选关键字段方便阅读
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
            app, sid, author, content_json = row
            print(f"[app={app} sid={sid} author={author}] content={content_json}")
        conn.close()
    except Exception as e:
        print(f"⚠️ 读取 SQLite 失败: {e}")

    print("\n✅ stateful_db.py: main() 执行结束")


if __name__ == "__main__":
    print("✅ 通过 __main__ 入口运行 stateful_db.py")
    asyncio.run(main())
