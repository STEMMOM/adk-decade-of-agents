"""
P14 — Session Isolation Test (Parallel Universes)

Goal:
1. Create two entirely separate sessions (A, B)
2. In Session A: tell the agent the user's name, then ask it back
3. In Session B: ask for the name without having introduced it
4. Print Session.events for both sessions to verify they are fully isolated
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "agents"
USER_ID = "susan"


async def send_one(runner: Runner, session_id: str, query: str) -> None:
    """Send a single message and print the model's reply."""
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
            text = event.content.parts[0].text
            if text and text != "None":
                print(f"{MODEL_NAME}[{session_id}] > {text}")


async def main() -> None:
    print("✅ P14 — session_isolation_test: main() starting")

    # 1. Create Agent and In-Memory SessionService
    agent = LlmAgent(
        model=Gemini(model=MODEL_NAME),
        name="isolation_agent",
        description="Session isolation test agent.",
    )
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # ---------- Session A ----------
    sessionA = "session-A"
    print(f"\n🔵 Creating Session A: {sessionA}")
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=sessionA,
    )

    await send_one(runner, sessionA, "Hi, I am Sam!")
    await send_one(runner, sessionA, "What is my name?")

    # ---------- Session B ----------
    sessionB = "session-B"
    print(f"\n🟣 Creating Session B: {sessionB}")
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=sessionB,
    )

    # In B: the agent should NOT know the name
    await send_one(runner, sessionB, "Hello, what is my name?")

    # ---------- Print events for both sessions ----------
    print("\n--- SESSION A EVENTS ---")
    session_A_data = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=sessionA,
    )
    for idx, e in enumerate(session_A_data.events):
        content = ""
        if e.content and getattr(e.content, "parts", None):
            content = e.content.parts[0].text
        print(f"- [{idx}] {e.author}: {content}")

    print("\n--- SESSION B EVENTS ---")
    session_B_data = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=sessionB,
    )
    for idx, e in enumerate(session_B_data.events):
        content = ""
        if e.content and getattr(e.content, "parts", None):
            content = e.content.parts[0].text
        print(f"- [{idx}] {e.author}: {content}")

    print("\n✅ Session Isolation Test finished.")


if __name__ == "__main__":
    asyncio.run(main())
