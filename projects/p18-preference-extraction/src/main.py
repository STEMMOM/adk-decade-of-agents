#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目 18：Preference Extraction v1（偏好抽取）
-----------------------------------------
目标：
1. 从 P17 的 Memory Schema v1 中读取 memory_store.json
2. 遍历 conversation_summaries[].summary_text
3. 使用简单可解释的规则，抽取：
   - Answer style / interaction style
   - 输出格式偏好（bullet points, code examples, clear reasoning）
   - 兴趣（sci-fi, agent projects, math/logic games）
   - Anti-Preferences（vague explanations, noisy UX, over-marketing, shallow hacks）
4. 将结果写入：
   memory["preferences"] = [ {key, value, confidence, source}, ... ]
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent  # projects/p18-preference-extraction
MEMORY_FILE = BASE_DIR / "memory_store.json"


# ============ 基础读写函数 ============

def load_memory() -> Dict[str, Any]:
    print(f"📥 Loading memory from: {MEMORY_FILE}")
    if not MEMORY_FILE.exists():
        print("⚠️ memory_store.json not found. Using empty memory.")
        return {}
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                print("✅ Memory loaded successfully.")
                return data
    except Exception as e:
        print("⚠️ Failed to read memory_store.json:", repr(e))
    return {}


def save_memory(memory: Dict[str, Any]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved updated memory to: {MEMORY_FILE}")


# ============ 偏好抽取逻辑 ============

def add_preference_if_new(
    prefs: List[Dict[str, Any]],
    seen: set,
    key: str,
    value: Any,
    confidence: float,
    source: str,
) -> None:
    """避免重复的 helper。"""
    sig = (key, json.dumps(value, sort_keys=True, ensure_ascii=False))
    if sig in seen:
        return
    prefs.append(
        {
            "key": key,
            "value": value,
            "confidence": confidence,
            "source": source,
        }
    )
    seen.add(sig)


def extract_preferences_from_summary(summary_text: str, source: str) -> List[Dict[str, Any]]:
    """
    从一条 summary_text 中抽取偏好。
    - 这里使用 rule-based（关键词匹配）方案，便于解释与后续调整。
    """
    prefs: List[Dict[str, Any]] = []
    text = summary_text
    lower = summary_text.lower()

    # 1) Answer style / interaction style
    if "concise" in lower and "structured" in lower and "answers" in lower:
        add_preference_if_new(
            prefs,
            set(),
            key="answer_style",
            value="concise, highly structured answers with clear reasoning and examples",
            confidence=0.95,
            source=source,
        )

    # 2) Format preferences: bullet points / code examples / clear reasoning
    format_values: List[str] = []
    if "bullet points" in lower:
        format_values.append("bullet_points")
    if "code examples" in lower:
        format_values.append("code_examples")
    if "clear reasoning" in lower:
        format_values.append("clear_reasoning")

    if format_values:
        add_preference_if_new(
            prefs,
            set(),
            key="format_preferences",
            value=format_values,
            confidence=0.9,
            source=source,
        )

    # 3) Interests / hobbies
    interests: List[str] = []
    if "reading sci-fi" in lower or "reading science fiction" in lower:
        interests.append("reading_sci_fi")
    if "building agent projects" in lower or "building small agent projects" in lower:
        interests.append("building_agent_projects")
    if "math/logic games" in lower or "math and logic games" in lower:
        interests.append("math_logic_games_with_children")

    if interests:
        add_preference_if_new(
            prefs,
            set(),
            key="interests",
            value=interests,
            confidence=0.85,
            source=source,
        )

    # 4) Values & Anti-Preferences（这里只抽 anti 部分，values 放到 P19）
    dislikes: List[str] = []
    if "vague, hand-wavy explanations" in lower or "vague explanations" in lower:
        dislikes.append("vague_explanations")
    if "noisy ux" in lower:
        dislikes.append("noisy_ux")
    if "over-marketing" in lower:
        dislikes.append("over_marketing")
    if "shallow \"productivity hacks\"" in lower or "shallow 'productivity hacks'" in lower:
        dislikes.append("shallow_productivity_hacks")

    if dislikes:
        add_preference_if_new(
            prefs,
            set(),
            key="dislikes",
            value=dislikes,
            confidence=0.9,
            source=source,
        )

    return prefs


def extract_preferences(memory: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    从 memory["conversation_summaries"] 中抽取偏好，填充到 memory["preferences"]。
    返回 (updated_memory, debug_info)
    """
    debug: Dict[str, Any] = {
        "existing_preferences": 0,
        "new_preferences": 0,
        "conversation_summaries_seen": 0,
    }

    conv_summaries = memory.get("conversation_summaries", [])
    if not isinstance(conv_summaries, list):
        print("⚠️ conversation_summaries is not a list. Nothing to extract.")
        return memory, debug

    # 确保 preferences 存在
    prefs: List[Dict[str, Any]] = memory.setdefault("preferences", [])
    seen = set()
    # 先把已有的 preferences 放入 seen，避免重复
    for p in prefs:
        sig = (p.get("key"), json.dumps(p.get("value"), sort_keys=True, ensure_ascii=False))
        seen.add(sig)

    debug["existing_preferences"] = len(prefs)

    for idx, entry in enumerate(conv_summaries):
        if not isinstance(entry, dict):
            continue
        summary_text = entry.get("summary_text") or ""
        if not summary_text:
            continue

        debug["conversation_summaries_seen"] += 1
        source = f"conversation_summaries[{idx}]"

        extracted = extract_preferences_from_summary(summary_text, source)
        for pref in extracted:
            sig = (pref["key"], json.dumps(pref["value"], sort_keys=True, ensure_ascii=False))
            if sig in seen:
                continue
            prefs.append(pref)
            seen.add(sig)
            debug["new_preferences"] += 1

    return memory, debug


# ============ 打印函数 ============

def print_debug_info(memory: Dict[str, Any], debug: Dict[str, Any]) -> None:
    print("\n🧬 Preference Extraction Summary")
    print("--------------------------------")
    print(f"- conversation_summaries seen: {debug.get('conversation_summaries_seen', 0)}")
    print(f"- existing preferences: {debug.get('existing_preferences', 0)}")
    print(f"- new preferences extracted: {debug.get('new_preferences', 0)}")
    print(f"- total preferences: {len(memory.get('preferences', []))}")

    print("\n📚 preferences (truncated preview):")
    prefs = memory.get("preferences", [])
    preview = json.dumps(prefs, ensure_ascii=False, indent=2)
    print(preview[:1000], "...\n")


# ============ 主函数 ============

def main():
    print("🚀 P18 — Preference Extraction v1 started")

    memory = load_memory()

    print("\n📦 Current memory (truncated preview):")
    preview = json.dumps(memory, ensure_ascii=False, indent=2)
    print(preview[:600], "...\n")

    updated_memory, debug = extract_preferences(memory)
    save_memory(updated_memory)
    print_debug_info(updated_memory, debug)

    print("🏁 P18 — Preference Extraction v1 finished")


if __name__ == "__main__":
    main()
