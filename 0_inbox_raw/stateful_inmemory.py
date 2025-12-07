# sessions_day3/stateful_inmemory.py

import asyncio
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Constants
MODEL_NAME = "gemini-2.5-flash-lite"
# 关键点：让 APP_NAME 和 ADK 默认一致，避免 App name mismatch 提示
APP_NAME = "agents"
USER_ID = "susan"


async def main() -> None:
    print("✅ stateful_inmemory.py: main() 开始执行")

    agent = LlmAgent(
        model=Gemini(model=MODEL_NAME),
        name="inmemory_agent",
        description="Simple agent using InMemorySessionService.",
    )

    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    session_id = "inmemory-demo"

    try:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        print(f"✅ 新建 Session: {session_id}")
    except Exception:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        print(f"♻️ 复用已有 Session: {session_id}")

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

    await send_one(msg1)
    await send_one(msg2)

    # 👇 这一块就是你要插入的 session dump，要和上面保持同一级缩进
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    print("\n--- SESSION EVENTS ---")
    for e in session.events:
        print(e)

    print("\n--- SESSION STATE ---")
    print(session.state)
    # 👆 一直到这里，都在 main() 里面

    print("\n✅ stateful_inmemory.py: main() 执行结束")


if __name__ == "__main__":
    print("✅ 通过 __main__ 入口运行 stateful_inmemory.py")
    asyncio.run(main())
