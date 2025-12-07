from pathlib import Path
import json
from typing import Any, Dict, List, Tuple, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_FILE = BASE_DIR / "memory_store.json"
PERSONA_FILE = BASE_DIR / "persona_state.json"


def load_memory(path: Path) -> Dict[str, Any]:
    """Load memory_store.json; return empty skeleton if missing or invalid."""
    print(f"📥 Loading memory from: {path}")
    if not path.exists():
        print("⚠️ memory_store.json not found. Using empty memory skeleton.")
        return {
            "schema_version": "1.0",
            "user_profile": {},
            "conversation_summaries": [],
            "preferences": [],
        }

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print("✅ Memory loaded successfully.")
        return data
    except Exception as e:
        print(f"❌ Failed to load memory_store.json: {e}")
        print("⚠️ Falling back to empty memory skeleton.")
        return {
            "schema_version": "1.0",
            "user_profile": {},
            "conversation_summaries": [],
            "preferences": [],
        }


def get_preferences(memory: Dict[str, Any]) -> List[Dict[str, Any]]:
    prefs = memory.get("preferences", [])
    if not isinstance(prefs, list):
        print("⚠️ `preferences` is not a list in memory_store.json, ignoring.")
        return []
    return prefs


def aggregate_list_values(
    prefs: List[Dict[str, Any]], target_key: str
) -> Tuple[List[Any], float, List[str]]:
    """
    Collect all list-type values for a given key across preferences.
    Returns (unique_values, max_confidence, sources).
    """
    values: List[Any] = []
    max_conf = 0.0
    sources: List[str] = []

    for pref in prefs:
        if pref.get("key") != target_key:
            continue

        value = pref.get("value")
        conf = float(pref.get("confidence", 0.5))
        src = str(pref.get("source", "unknown"))

        # normalize to list
        if isinstance(value, list):
            candidates = value
        else:
            candidates = [value]

        for v in candidates:
            if v is None:
                continue
            if v not in values:
                values.append(v)

        if conf > max_conf:
            max_conf = conf
        if src not in sources:
            sources.append(src)

    return values, max_conf, sources


def aggregate_scalar_value(
    prefs: List[Dict[str, Any]], target_key: str
) -> Tuple[Optional[Any], float, List[str]]:
    """
    Pick the highest-confidence scalar value for a key.
    Returns (best_value, best_confidence, sources_for_that_value).
    """
    best_value = None
    best_conf = 0.0
    sources: List[str] = []

    for pref in prefs:
        if pref.get("key") != target_key:
            continue

        value = pref.get("value")
        conf = float(pref.get("confidence", 0.5))
        src = str(pref.get("source", "unknown"))

        # skip list values here; this aggregator is for scalar-ish ones
        if isinstance(value, list):
            continue

        if best_value is None or conf > best_conf:
            best_value = value
            best_conf = conf
            sources = [src]
        elif value == best_value and src not in sources:
            # same value, add more sources
            sources.append(src)

    return best_value, best_conf, sources


def build_persona(
    preferences: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a persona_state.json-style structure from preferences + user_profile.

    This is where we define the v1 Persona schema.
    """
    print("🎭 Building persona from preferences + user_profile ...")

    # Identity basics from user_profile if present
    name = user_profile.get("name") or user_profile.get("full_name")
    country = user_profile.get("country")
    locale = user_profile.get("locale")

    # Aggregate preferences into fields
    interests, interests_conf, interests_src = aggregate_list_values(
        preferences, "interests"
    )
    dislikes, dislikes_conf, dislikes_src = aggregate_list_values(
        preferences, "dislikes"
    )
    fmt_prefs, fmt_conf, fmt_src = aggregate_list_values(
        preferences, "format_preferences"
    )
    answer_style, style_conf, style_src = aggregate_scalar_value(
        preferences, "answer_style"
    )

    persona_id = "persona_default_v1"
    if name:
        persona_id = f"persona_{str(name).lower().replace(' ', '_')}_v1"

    # Build persona description (language layer)
    desc_parts = []
    if name:
        desc_parts.append(f"This user is {name}.")
    if country:
        desc_parts.append(f"They are based in {country}.")
    if interests:
        desc_parts.append(
            "They are especially interested in: "
            + ", ".join(str(i) for i in interests)
            + "."
        )
    if answer_style:
        desc_parts.append(f"They prefer answers that are: {answer_style}.")
    if dislikes:
        desc_parts.append(
            "They strongly dislike: "
            + ", ".join(str(d) for d in dislikes)
            + "."
        )

    description = " ".join(desc_parts) if desc_parts else "No explicit persona description yet."

    persona = {
        "id": persona_id,
        "name": name or "Unknown User",
        "country": country,
        "locale": locale,
        "description": description,
        "interests": interests,
        "interests_confidence": interests_conf,
        "dislikes": dislikes,
        "dislikes_confidence": dislikes_conf,
        "format_preferences": fmt_prefs,
        "format_preferences_confidence": fmt_conf,
        "answer_style": answer_style,
        "answer_style_confidence": style_conf,
        # For traceability we keep a map from field → preference sources
        "sources": {
            "interests": interests_src,
            "dislikes": dislikes_src,
            "format_preferences": fmt_src,
            "answer_style": style_src,
        },
    }

    return persona


def save_persona(path: Path, persona: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(persona, f, ensure_ascii=False, indent=2)
    print(f"💾 Persona saved to: {path}")


def print_persona_summary(persona: Dict[str, Any]) -> None:
    print("\n🎭 Persona Summary")
    print("------------------")
    print(f" id:        {persona.get('id')}")
    print(f" name:      {persona.get('name')}")
    if persona.get("country"):
        print(f" country:   {persona.get('country')}")
    if persona.get("locale"):
        print(f" locale:    {persona.get('locale')}")
    print()

    interests = persona.get("interests") or []
    dislikes = persona.get("dislikes") or []
    fmt_prefs = persona.get("format_preferences") or []
    answer_style = persona.get("answer_style")

    print(f" interests ({len(interests)}): {interests}")
    print(f" dislikes  ({len(dislikes)}): {dislikes}")
    print(f" format_preferences ({len(fmt_prefs)}): {fmt_prefs}")
    print(f" answer_style: {answer_style}")
    print()
    print(" description:")
    print("  " + (persona.get("description") or "").strip())
    print()


def main() -> None:
    print("🚀 P19 — Preference-Aware Persona v1 started")

    # 1. Load memory
    memory = load_memory(MEMORY_FILE)

    # 2. Get preferences
    preferences = get_preferences(memory)
    user_profile = memory.get("user_profile", {}) or {}

    print("\n🧬 Preference Input")
    print("-------------------")
    print(f"- preferences found: {len(preferences)}")
    print(f"- user_profile keys: {list(user_profile.keys())}")

    if not preferences:
        print("⚠️ No preferences found in memory_store.json.")
        print("   P19 can still build a very minimal persona from user_profile, if available.\n")

    # 3. Build persona
    persona = build_persona(preferences, user_profile)

    # 4. Save persona_state.json
    save_persona(PERSONA_FILE, persona)

    # 5. Print human-readable summary
    print_persona_summary(persona)

    print("🏁 P19 — Preference-Aware Persona v1 finished")


if __name__ == "__main__":
    main()
