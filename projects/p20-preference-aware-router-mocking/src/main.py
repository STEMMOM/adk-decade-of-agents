from pathlib import Path
import json
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent.parent
PERSONA_FILE = BASE_DIR / "persona_state.json"


def load_persona(path: Path) -> Dict[str, Any]:
    print(f"📥 Loading persona from: {path}")
    if not path.exists():
        print("❌ persona_state.json not found. Please run P19 first.")
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
    This is v1, intentionally simple and explainable.
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

    # Heuristics for structured output
    if "structured" in answer_style or "concise" in answer_style:
        policy["prefer_structured_output"] = True
    if any("bullet" in str(x).lower() for x in fmt_prefs):
        policy["prefer_structured_output"] = True
    if any("code" in str(x).lower() for x in fmt_prefs):
        policy["prefer_code_examples"] = True

    # Heuristics for avoiding marketing style
    if any("marketing" in str(x).lower() for x in dislikes):
        policy["avoid_marketing_style"] = True

    # Default agent decision
    if policy["prefer_structured_output"]:
        policy["default_agent"] = "structured_agent"
    else:
        policy["default_agent"] = "narrative_agent"

    return policy


def structured_agent_respond(query: str, persona: Dict[str, Any]) -> str:
    """
    Simulated 'structured' agent: bullet points, clear reasoning focus.
    In a future version, this would call a real ADK agent.
    """
    interests = persona.get("interests") or []
    answer_style = persona.get("answer_style") or "concise, structured"

    lines = [
        f"Structured Agent Response",
        f"- Style: {answer_style}",
        f"- Known interests: {', '.join(interests) if interests else 'N/A'}",
        "",
        f"Answer to: {query}",
        "1) First, summarize the core idea.",
        "2) Then, break it into clear, ordered steps.",
        "3) Finally, suggest one concrete next action.",
    ]
    return "\n".join(lines)


def narrative_agent_respond(query: str, persona: Dict[str, Any]) -> str:
    """
    Simulated 'narrative' agent: more free-form, story-like explanation.
    """
    interests = persona.get("interests") or []
    lines = [
        "Narrative Agent Response",
        f"(This agent prefers a more story-like, exploratory explanation.)",
        f"Interests I know about you: {', '.join(interests) if interests else 'N/A'}",
        "",
        f"Let me walk you through this step by step, in a more narrative way, for the question:",
        f"\"{query}\"",
    ]
    return "\n".join(lines)


def print_persona_signals(persona: Dict[str, Any]) -> None:
    print("\n🎭 Persona Signals")
    print("------------------")
    print(f"- answer_style: {persona.get('answer_style')}")
    print(f"- format_preferences: {persona.get('format_preferences')}")
    print(f"- dislikes: {persona.get('dislikes')}")


def print_policy(policy: Dict[str, Any]) -> None:
    print("\n🧭 Routing Decision")
    print("-------------------")
    for k, v in policy.items():
        print(f"- {k}: {v}")
    print(f"→ selected agent: {policy.get('default_agent')}")


def main() -> None:
    print("🚀 P20 — Preference-Aware Router v1 started")

    # 1. Load persona
    persona = load_persona(PERSONA_FILE)
    if not persona:
        print("⚠️ No persona loaded. Exiting.")
        return

    # 2. Inspect signals
    print_persona_signals(persona)

    # 3. Derive routing policy
    policy = derive_policy(persona)
    print_policy(policy)

    # 4. Demo query (in a real project, this would come from user input)
    demo_query = "Explain what this ADK project does for the next decade of agents."

    # 5. Route to agent
    agent_name = policy.get("default_agent")
    print("\n🤖 Agent Response")
    print("-----------------")

    if agent_name == "structured_agent":
        response = structured_agent_respond(demo_query, persona)
    else:
        response = narrative_agent_respond(demo_query, persona)

    print(response)
    print("\n🏁 P20 — Preference-Aware Router v1 finished")


if __name__ == "__main__":
    main()
