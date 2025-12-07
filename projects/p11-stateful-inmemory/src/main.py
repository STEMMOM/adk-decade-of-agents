import asyncio
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types  # 用来构造 Content / Part — Used to construct Content/Part

MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "agents"
USER_ID = "susan"
SESSION_ID = "p11-inmemory-demo"


async def ask_agent(runner: Runner, message: str) -> str:
    """
    给定一条用户文本，调用 runner.run_async，从事件流中提取最终回答的 text 并返回。
    Provide a user message, call runner.run_async, and return the final response text from the event stream.
    """
    print(f"\nUser[{SESSION_ID}] > {message}")

    # ADK 正确的消息结构：Content + Part(text=...) — Proper ADK message structure
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    final_text = "No final response."

    # 关键点：使用 run_async + 关键字参数 new_message — Key: use run_async with the new_message keyword arg
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text
            break

    print(f"AI[{SESSION_ID}]   > {final_text}")
    return final_text


async def main() -> None:
    print("✅ P11 — stateful_inmemory: main() starting")

    # 1. 创建 Agent — Create agent
    agent = LlmAgent(
        model=Gemini(model=MODEL_NAME),
        name="inmemory_agent",
        description="Simple agent using InMemorySessionService.",
    )

    # 2. 创建 SessionService（内存型）— Create in-memory SessionService
    session_service = InMemorySessionService()

    # 3. 显式创建一个 Session（方便之后 get_session 和观察 events）— Explicitly create a session for later inspection
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    print(f"🧠 Created session: id={session.id}, user_id={session.user_id}")

    # 4. 创建 Runner（调度器）— Create runner (orchestrator)
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # 5. 第一轮：告诉它你的名字 — First turn: tell it your name
    await ask_agent(runner, "My name is Sam!")

    # 6. 第二轮：问它你是谁 — Second turn: ask who you are
    await ask_agent(runner, "What is my name?")

    # 7. 打印 Session.events（事件时间线）— Print Session.events timeline
    print("\n📜 Session Dump — events timeline:")
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    for idx, event in enumerate(session.events):
        author = event.author
        content = event.content

        text = ""
        # content 是 Content 对象：取第一个 part 的 text — content is Content: grab first part text
        if content and getattr(content, "parts", None):
            part0 = content.parts[0]
            # 部分版本里 text 在 part0.text — Some versions store text in part0.text
            text = getattr(part0, "text", "")

        print(f"- [{idx}] {author}: {text}")


if __name__ == "__main__":
    asyncio.run(main())
