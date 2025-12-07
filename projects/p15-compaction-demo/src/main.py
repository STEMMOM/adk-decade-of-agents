"""
P15 — Context Compaction Demo (Automatic Summarization)

This project demonstrates ADK's built-in EventsCompactionConfig,
which automatically summarizes long Session timelines into lower entropy
summary events.
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

MODEL_NAME = "gemini-2.5-flash-lite"
USER_ID = "susan"


async def send_one(runner: Runner, session_id: str, query: str):
    """Send a message and print the final model response."""
    print(f"\nUser[{session_id}] > {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=content,
    ):
        if event.content and event.content.parts:
            msg = event.content.parts[0].text
            if msg and msg != "None":
                print(f"{MODEL_NAME}[{session_id}] > {msg}")


async def main():
    print("🚀 P15 — compaction_demo: starting")

    # --- Step 1: Create Agent ---
    agent = LlmAgent(
        model=Gemini(model=MODEL_NAME),
        name="compaction_agent",
        description="Agent with automatic context compaction.",
    )
    print("✅ Agent created: compaction_agent")

    # --- Step 2: Create App with Compaction Enabled ---
    compaction_app = App(
        name="compaction_app",
        root_agent=agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=3,   # Trigger summary every 3 events
            overlap_size=1,          # Retain 1 recent original event
        ),
    )
    print("✅ App created with compaction enabled")

    # --- Step 3: Create Session & Runner ---
    session_service = InMemorySessionService()
    runner = Runner(app=compaction_app, session_service=session_service)
    session_id = "compaction-session"
    app_name = compaction_app.name

    try:
        await session_service.create_session(
            app_name=app_name,
            user_id=USER_ID,
            session_id=session_id,
        )
        print(f"🆕 Created session: {session_id}")
    except Exception:
        print(f"♻️ Reusing session: {session_id}")

    # --- Step 4: Trigger multiple rounds (compaction at 3rd message) ---
    print("\n🔄 Sending multiple messages to trigger compaction")
    await send_one(runner, session_id, "Explain AI in healthcare.")
    await send_one(runner, session_id, "Tell me more about drug discovery.")
    await send_one(runner, session_id, "Explain the second point again.")
    await send_one(runner, session_id, "Who are the key companies involved?")

    # --- Step 5: Inspect compaction event ---
    print("\n📦 Checking for compaction event")
    session = await session_service.get_session(
        app_name=app_name,
        user_id=USER_ID,
        session_id=session_id,
    )

    found = False

    for event in session.events:
        if event.actions and event.actions.compaction:
            found = True
            print("\n🎉 Compaction event detected!\n")

            comp = event.actions.compaction
            compacted = getattr(comp, "compacted_content", None)

            summary_text = ""

            # Case 1: Content object
            if hasattr(compacted, "parts"):
                parts = compacted.parts
                if parts and hasattr(parts[0], "text"):
                    summary_text = parts[0].text

            # Case 2: dict format
            elif isinstance(compacted, dict):
                parts = compacted.get("parts", [])
                if parts and isinstance(parts[0], dict):
                    summary_text = parts[0].get("text", "")

            else:
                summary_text = str(compacted)

            print("📝 Summary Content:\n")
            print(summary_text[:800] + ("..." if len(summary_text) > 800 else ""))
            break

    if not found:
        print("⚠️ No compaction event found — try more messages.")

    print("\n🏁 P15 — compaction_demo finished.")


if __name__ == "__main__":
    print("👉 Running P15 via __main__")
    asyncio.run(main())
