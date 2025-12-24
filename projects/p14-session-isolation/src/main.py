"""
P14 — Session Isolation Test (Parallel Universes)

Goal:
1. Create two entirely separate sessions (A, B)
2. In Session A: tell the agent the user's name, then ask it back
3. In Session B: ask for the name without having introduced it
4. Print Session.events for both sessions to verify they are fully isolated
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

USE_MOCK = True  # 默认使用 Mock，避免真实 LLM 依赖；设置为 False 可恢复原 ADK 路径

if not USE_MOCK:
    from google.adk.agents import LlmAgent
    from google.adk.models.google_llm import Gemini
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import Runner
    from google.genai import types

MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "agents"
USER_ID = "susan"


# -------------------- Mock Runner --------------------
@dataclass
class MockEvent:
    session_id: str
    role: str
    text: str


class MockSession:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.events: List[MockEvent] = []


class MockSessionService:
    def __init__(self) -> None:
        self._sessions: Dict[str, MockSession] = {}

    async def create_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        self._sessions[session_id] = MockSession(session_id)

    async def get_session(self, *, app_name: str, user_id: str, session_id: str) -> MockSession:
        return self._sessions[session_id]


class MockRunner:
    """
    Minimal deterministic mock runner for session isolation regression.
    Per-session history is isolated by session_id.
    """

    def __init__(self, session_service: MockSessionService) -> None:
        self.session_service = session_service
        self.history: Dict[str, List[str]] = {}

    async def run_async(self, *, session_id: str, user_text: str, **kwargs: Any) -> AsyncGenerator[MockEvent, None]:
        hist = self.history.setdefault(session_id, [])
        hist.append(user_text)

        user_event = MockEvent(session_id=session_id, role="user", text=user_text)
        reply = f"[MOCK][{session_id}] turn={len(hist)} echo: {user_text}"
        assistant_event = MockEvent(session_id=session_id, role="assistant", text=reply)

        # Persist into session events list for later inspection
        session = await self.session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
        session.events.append(user_event)
        session.events.append(assistant_event)

        yield user_event
        yield assistant_event


# -------------------- Shared send_one --------------------
async def send_one(runner: Any, session_id: str, query: str) -> None:
    """Send a single message and print the model's reply (mock or real)."""
    print(f"\nUser[{session_id}] > {query}")

    if USE_MOCK:
        async for event in runner.run_async(session_id=session_id, user_text=query):
            if event.role == "assistant":
                print(f"{MODEL_NAME}[{session_id}] > {event.text}")
        return

    # Real path (kept for future use)
    content = types.Content(role="user", parts=[types.Part(text=query)])
    async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=content):
        if event.content and event.content.parts:
            text = event.content.parts[0].text
            if text and text != "None":
                print(f"{MODEL_NAME}[{session_id}] > {text}")


# -------------------- Main --------------------
async def main() -> None:
    print("✅ P14 — session_isolation_test: main() starting")

    if USE_MOCK:
        session_service = MockSessionService()
        runner = MockRunner(session_service)
    else:
        agent = LlmAgent(
            model=Gemini(model=MODEL_NAME),
            name="isolation_agent",
            description="Session isolation test agent.",
        )
        session_service = InMemorySessionService()
        runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

    # ---------- Session A ----------
    sessionA = "session-A"
    print(f"\n🔵 Creating Session A: {sessionA}")
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=sessionA)

    await send_one(runner, sessionA, "Hi, I am Sam!")
    await send_one(runner, sessionA, "What is my name?")

    # ---------- Session B ----------
    sessionB = "session-B"
    print(f"\n🟣 Creating Session B: {sessionB}")
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=sessionB)

    # In B: the agent should NOT know the name
    await send_one(runner, sessionB, "Hello, what is my name?")

    # ---------- Print events for both sessions ----------
    print("\n--- SESSION A EVENTS ---")
    session_A_data = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=sessionA)
    for idx, e in enumerate(session_A_data.events):
        print(f"- [{idx}] {e.role}[{e.session_id}]: {getattr(e, 'text', '')}")

    print("\n--- SESSION B EVENTS ---")
    session_B_data = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=sessionB)
    for idx, e in enumerate(session_B_data.events):
        print(f"- [{idx}] {e.role}[{e.session_id}]: {getattr(e, 'text', '')}")

    print("\n✅ Session Isolation Test finished.")


if __name__ == "__main__":
    asyncio.run(main())
