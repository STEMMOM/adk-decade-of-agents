import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part


# --- Constants you may want to customize ---
APP_NAME = "p20_preference_router_adk"
USER_ID = "persona_user"
SESSION_ID = "p20_adk_demo_session"
MODEL = "gemini-2.0-flash"  # Use a valid model ID for your ADK setup

BASE_DIR = Path(__file__).resolve().parent.parent
PERSONA_FILE = BASE_DIR / "persona_state.json"


# --------------------------
# Loading & Policy Derivation
# --------------------------

def load_persona(path: Path) -> Dict[str, Any]:
    print(f"📥 Loading persona from: {path}")
    if not path.exists():
        print("❌ persona_state.json not found. Please run P19 and/or copy the file here.")
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print("✅ Persona loaded successfully.")
        return data
    except Exception as e:
        print(f"❌ Failed to load persona_state.json: {e}")
        return {}


def derive_policy(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive a minimal routing policy from persona fields.
    Mirrors the logic used in the mocking version.
    """
    answer_style = str(persona.get("answer_style") or "").lower()
    fmt_prefs: List[str] = persona.get("format_preferences") or []
    dislikes: List[str] = persona.get("dislikes") or []

    policy: Dict[str, Any] = {
        "prefer_structured_output": False,
        "avoid_marketing_style": False,
        "prefer_code_examples": False,
        "default_agent": "narrative_agent",
    }

    # Heuristic: if persona likes "concise" / "structured", prefer structured output
    if "structured" in answer_style or "concise" in answer_style:
        policy["prefer_structured_output"] = True

    # Heuristic: if persona has bullet points / code in format preferences
    if any("bullet" in str(x).lower() for x in fmt_prefs):
        policy["prefer_structured_output"] = True
    if any("code" in str(x).lower() for x in fmt_prefs):
        policy["prefer_code_examples"] = True

    # Heuristic: avoid marketing style if dislikes mention it
    if any("marketing" in str(x).lower() for x in dislikes):
        policy["avoid_marketing_style"] = True

    # Final agent choice
    if policy["prefer_structured_output"]:
        policy["default_agent"] = "structured_agent"
    else:
        policy["default_agent"] = "narrative_agent"

    return policy


def print_persona_signals(persona: Dict[str, Any]) -> None:
    print("\n🎭 Persona Signals")
    print("------------------")
    print(f"- answer_style: {persona.get('answer_style')}")
    print(f"- format_preferences: {persona.get('format_preferences')}")
    print(f"- dislikes: {persona.get('dislikes')}")


def print_policy(policy: Dict[str, Any]) -> None:
    print("\n🧭 Routing Policy")
    print("-----------------")
    for k, v in policy.items():
        print(f"- {k}: {v}")
    print(f"→ selected agent: {policy.get('default_agent')}")


# --------------------------
# ADK Agent Construction
# --------------------------

def build_structured_instruction(persona: Dict[str, Any]) -> str:
    """
    Build an instruction string for the structured agent,
    taking Persona into account.
    """
    base = [
        "You are a structured assistant.",
        "Always respond concisely with clear reasoning and explicit structure.",
        "Use numbered steps and bullet points whenever helpful.",
    ]
    fmt_prefs = persona.get("format_preferences") or []
    dislikes = persona.get("dislikes") or []

    if any("code" in str(x).lower() for x in fmt_prefs):
        base.append("Include small, focused code examples when appropriate.")
    if any("marketing" in str(x).lower() for x in dislikes):
        base.append("Avoid any marketing-style language or sales tone.")

    description = persona.get("description")
    if description:
        base.append("")
        base.append("Persona description:")
        base.append(description)

    return " ".join(base)


def build_narrative_instruction(persona: Dict[str, Any]) -> str:
    """
    Build an instruction string for the narrative agent.
    """
    base = [
        "You are an explanatory, narrative-style assistant.",
        "Give well-structured but more free-form, story-like explanations.",
        "Use paragraphs and examples rather than strict bullet lists.",
    ]
    dislikes = persona.get("dislikes") or []
    if any("marketing" in str(x).lower() for x in dislikes):
        base.append("Avoid marketing-style language or hype.")

    description = persona.get("description")
    if description:
        base.append("")
        base.append("Persona description:")
        base.append(description)

    return " ".join(base)


def create_agents(persona: Dict[str, Any]) -> Dict[str, LlmAgent]:
    structured = LlmAgent(
        name="structured_agent",
        model=MODEL,
        instruction=build_structured_instruction(persona),
        description="Answers concisely with bullet points and clear reasoning.",
    )

    narrative = LlmAgent(
        name="narrative_agent",
        model=MODEL,
        instruction=build_narrative_instruction(persona),
        description="Provides more narrative, exploratory explanations.",
    )

    return {
        "structured_agent": structured,
        "narrative_agent": narrative,
    }


# --------------------------
# ADK Runner Execution
# --------------------------

async def run_with_adk(
    chosen_agent: LlmAgent,
    demo_query: str,
) -> str:
    """
    Run the chosen ADK agent with a simple single-turn query,
    and return the final response text.
    """
    session_service = InMemorySessionService()

    # Create a new session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    runner = Runner(
        agent=chosen_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    user_content = Content(
        parts=[Part(text=demo_query)],
        role="user",
    )

    final_response_text = "(no final response)"
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_content,
    ):
        # Following the pattern from ADK docs: check for final response
        if hasattr(event, "is_final_response") and event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text

    return final_response_text


# --------------------------
# Main Orchestration
# --------------------------

async def main_async() -> None:
    print("🚀 P20A — Preference-Aware Router (ADK) v1 started")

    # 1. Load persona
    persona = load_persona(PERSONA_FILE)
    if not persona:
        print("⚠️ No persona loaded. Exiting.")
        return

    # 2. Print persona signals
    print_persona_signals(persona)

    # 3. Derive routing policy
    policy = derive_policy(persona)
    print_policy(policy)

    # 4. Build ADK agents
    agents = create_agents(persona)
    agent_name = policy.get("default_agent", "narrative_agent")
    chosen_agent = agents.get(agent_name, agents["narrative_agent"])

    # 5. Demo query (can be replaced with user input later)
    demo_query = "Explain what this ADK project does for the next decade of agents."

    print("\n🤖 ADK Agent Response")
    print("---------------------")
    response_text = await run_with_adk(chosen_agent, demo_query)
    print(response_text)

    print("\n🏁 P20A — Preference-Aware Router (ADK) v1 finished")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
