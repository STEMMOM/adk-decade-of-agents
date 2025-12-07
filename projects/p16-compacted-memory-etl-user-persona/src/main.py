#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目 16：Compacted Memory ETL（人格摘要驱动的长期记忆）
Project 16: Compacted Memory ETL (long-term memory driven by persona summaries)

新版本目标：
New goals for this version:
1. 不再讲 AI in healthcare，而是讲“我是谁”
   Focus on “who am I” instead of “AI in healthcare.”
2. 让 Session.events + Compaction 生成一条结构化的人格摘要
   Use Session.events + Compaction to generate a structured persona summary.
3. 方便后续：
   Prepare for downstream work:
   - P17 做 Schema 升级 / Schema upgrade
   - P18 从 conversation_summaries 中抽取 Preferences / Values
     Extract Preferences / Values from conversation_summaries
   - P19 抽取 Knowledge / Work Style
     Extract Knowledge / Work Style
   - P20 生成 Persona Card
     Produce a Persona Card
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.runners import InMemoryRunner
from google.genai import types

MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "agents"
USER_ID = "susan"

BASE_DIR = Path(__file__).resolve().parent.parent  # projects/p16-compacted-memory-etl
MEMORY_FILE = BASE_DIR / "memory_store.json"
SYSTEM_INSTRUCTION = (
    "You are a profiling assistant that helps build a long-term user profile.\n"
    "Always respond in a CLEAR, STRUCTURED markdown format.\n\n"
    "Whenever the user asks for a summary of themselves, use EXACTLY these sections:\n"
    "## Identity\n"
    "- Name: ...\n"
    "- Country of origin: ...\n"
    "- Current location: ...\n\n"
    "## Background\n"
    "- Work / projects: ...\n\n"
    "## Interests\n"
    "- ...\n\n"
    "## Work Style\n"
    "- ...\n\n"
    "## Preferences\n"
    "- Answer style: ...\n"
    "- Content preferences: ...\n\n"
    "## Values\n"
    "- ...\n\n"
    "## Anti-Preferences\n"
    "- Things the user strongly dislikes: ...\n\n"
    "Be concise, but keep all important details the user mentioned. "
    "This summary will be stored as long-term memory and used to build a persona later."
)


# ==== Memory 读写 / Memory load & save ====

def load_memory_store() -> Dict[str, Any]:
    if MEMORY_FILE.exists():
        try:
            with MEMORY_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print("⚠️ 读取 memory_store.json 失败，将使用空结构 (Failed to read memory_store.json; using empty structure):", repr(e))
    return {"conversation_summaries": []}


def save_memory_store(data: Dict[str, Any]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 已写入 memory_store.json (memory_store.json written) -> {MEMORY_FILE}")


# ==== compaction 摘要抽取 / Extract compaction summaries ====

def _safe_get_actions(ev: Any) -> Optional[Dict[str, Any]]:
    actions = getattr(ev, "actions", None)
    if actions:
        if isinstance(actions, dict):
            return actions
        if hasattr(actions, "__dict__"):
            return actions.__dict__
    data = getattr(ev, "data", None)
    if isinstance(data, dict):
        return data.get("actions")
    return None


def extract_compaction_records_from_session(session: Any) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    for ev in session.events:
        actions = _safe_get_actions(ev)
        if not actions:
            continue
        compaction = actions.get("compaction") if isinstance(actions, dict) else None
        if not compaction:
            continue
        if not isinstance(compaction, dict) and hasattr(compaction, "__dict__"):
            compaction = compaction.__dict__
        compacted = compaction.get("compacted_content") if isinstance(compaction, dict) else None
        if not compacted:
            continue

        # 尝试解析 compacted_content 的文本 / Try to parse compacted_content text
        summary_text = None
        raw_struct: Any = {}

        if isinstance(compacted, str):
            summary_text = compacted
            raw_struct = {"text": compacted}
        elif hasattr(compacted, "parts"):
            try:
                parts = getattr(compacted, "parts", None)
                if parts and len(parts) > 0:
                    first = parts[0]
                    text_candidate = getattr(first, "text", None)
                    summary_text = text_candidate or str(compacted)
                else:
                    summary_text = str(compacted)
            except Exception:
                summary_text = str(compacted)
            raw_struct = {"repr": str(compacted)}
        elif isinstance(compacted, dict):
            parts = compacted.get("parts")
            text_candidate = None
            if isinstance(parts, list) and parts:
                first = parts[0]
                if isinstance(first, dict) and "text" in first:
                    text_candidate = first["text"]
            summary_text = text_candidate or compacted.get("text") or json.dumps(compacted, ensure_ascii=False)
            raw_struct = compacted
        else:
            summary_text = str(compacted)
            raw_struct = {"value": summary_text}

        ts = getattr(ev, "timestamp", None) or getattr(ev, "create_time", None)
        if isinstance(ts, (int, float)):
            created_at = datetime.fromtimestamp(ts).isoformat() + "Z"
        else:
            created_at = ts or datetime.utcnow().isoformat() + "Z"

        session_id = getattr(ev, "session_id", None) or getattr(session, "id", None)

        records.append(
            {
                "app_name": session.app_name,
                "user_id": session.user_id,
                "session_id": session_id,
                "created_at": created_at,
                "summary_text": summary_text,
                "raw": raw_struct,
            }
        )

    return records


def append_compaction_records_to_memory(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    memory = load_memory_store()
    conv_summaries: List[Dict[str, Any]] = memory.setdefault("conversation_summaries", [])

    for r in records:
        print("\n📝 抽取到一条 compaction 摘要 (extracted one compaction summary):")
        print(f"   session_id: {r['session_id']}")
        print(f"   created_at: {r['created_at']}")
        print(f"   summary_text (preview): {r['summary_text'][:160]}...")

        conv_summaries.append(r)

    save_memory_store(memory)
    return memory


# ==== 对话发送 / Send conversation turns ====

async def send_one(runner: InMemoryRunner, session_id: str, query: str):
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


# ==== 主函数 / Main ====

async def main():
    print("🚀 P16 — Compacted Persona Memory ETL Demo")

    # 1) Agent：改成“结构化人物画像助手” / Turn the agent into a structured persona assistant
    gemini_model = Gemini(model=MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)
    agent = LlmAgent(
        model=gemini_model,
        name="compaction_memory_agent",
        description="Agent that builds a structured user profile and produces compacted summaries.",
        tools=[],
    )
    print("✅ Agent 创建完成 (Agent created)：compaction_memory_agent")

    # 2) App + compaction / App with compaction enabled
    app = App(
        name=APP_NAME,
        root_agent=agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=3,
            overlap_size=1,
        ),
    )
    print("✅ App 创建完成（已启用 EventsCompactionConfig） / App created with EventsCompactionConfig enabled")

    runner = InMemoryRunner(app=app)
    print("✅ InMemoryRunner 创建完成 (InMemoryRunner created)")

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="compacted-persona-demo",
    )
    print(f"🆕 新建 session (new session): {session.id}")

    # 3) 新的人格主线对话 / Persona-focused dialogue
    queries = [
        "Hi, I'd like to build a personal profile that you can remember across sessions. I will tell you about myself. Just acknowledge and ask me to continue.",
        "My name is Susan. I was born in China, and now I live in the US. I work on AI, agents, and education-related projects.",
        "In my free time I love reading sci-fi, building small agent projects, and playing math and logic games with my kids.",
        "When I talk to an AI assistant, I prefer concise, highly structured answers with bullet points, code examples, and clear reasoning. I really dislike vague, hand-wavy explanations.",
        "I care a lot about intellectual honesty, structural thinking, and long-term reproducibility. I strongly dislike noisy UX, over-marketing, and shallow 'productivity hacks'.",
        "Please summarize my profile in a structured way with the following sections: Identity, Background, Interests, Work Style, Preferences, Values, and Anti-Preferences.",
    ]

    print("\n🔄 开始人格主线对话（将触发 compaction） / Start persona dialogue (will trigger compaction)")
    for q in queries:
        await send_one(runner, session.id, q)

    # 4) Dump 事件摘要 / Dump event summaries
    print("\n📦 Dump Session Events（摘要预览） / Session events preview")
    session = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    for e in session.events:
        author = getattr(e, "author", None) or getattr(e, "role", None)
        text = ""
        if getattr(e, "content", None) and getattr(e.content, "parts", None):
            part = e.content.parts[0]
            text = getattr(part, "text", "") or ""
        print(f"- [{author}] {text[:80]}...")

    # 5) 抽取 compaction.summary → 写入 memory_store.json / Extract compaction.summary and write to memory_store.json
    print("\n🔍 从 Session.events 中抽取 compaction.summary ... / Extracting compaction.summary from Session.events ...")
    records = extract_compaction_records_from_session(session)

    if not records:
        print("⚠️ 未发现任何 compaction 摘要记录。 / No compaction summaries found.")
        print("   你可以：调小 compaction_interval / 增加对话轮数 / 检查事件结构。 (Options: decrease compaction_interval, add more turns, or inspect event structure.)")
        print("   Suggestions: decrease compaction_interval, add more dialogue turns, or inspect event structure.")
    else:
        memory = append_compaction_records_to_memory(records)
        print("\n📚 当前 memory_store.json（截断预览） / Current memory_store.json (truncated preview):")
        preview = json.dumps(memory, ensure_ascii=False, indent=2)
        print(preview[:1000], "...\n")

    print("🏁 P16 — Compacted Persona Memory ETL Demo 完成 / Finished")


if __name__ == "__main__":
    print("👉 通过 __main__ 运行 P16（人格压缩示例） / Run P16 via __main__ (persona compaction demo)")
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ 程序异常 (Program error):", repr(e))
