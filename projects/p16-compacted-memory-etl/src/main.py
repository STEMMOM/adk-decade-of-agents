#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目 16：Compacted Memory ETL（压缩摘要驱动的长期记忆）
Project 16: Compacted Memory ETL (summary-driven long-term memory)

功能：
Features:
1. 用 App + EventsCompactionConfig 创建带自动压缩的 Agent 应用
   Build an agent App with automatic compaction via EventsCompactionConfig.
2. 用 InMemoryRunner 跑一段多轮对话，触发 compaction
   Run a multi-turn dialogue with InMemoryRunner to trigger compaction.
3. 从 session.events 中提取 compaction summary（actions.compaction.compacted_content）
   Extract compaction summaries from session.events (actions.compaction.compacted_content).
4. 把这些摘要写入 memory_store.json 的 conversation_summaries
   Write these summaries into memory_store.json under conversation_summaries.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.apps.app import App, EventsCompactionConfig  # ✅ ADK 中的正确 import / Correct ADK import
from google.adk.runners import InMemoryRunner
from google.genai import types

# ---- 全局常量 / Global constants ----
MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "agents"
USER_ID = "susan"

# projects/p16-compacted-memory-etl/src/main.py -> parent.parent = projects/p16-compacted-memory-etl
BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_FILE = BASE_DIR / "memory_store.json"


# ========== Memory Store 读写工具 / Utilities ==========

def load_memory_store() -> Dict[str, Any]:
    """读取 memory_store.json，没有就返回初始化结构。Read memory_store.json; return the default structure if missing."""
    if MEMORY_FILE.exists():
        try:
            with MEMORY_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print("⚠️ 读取 memory_store.json 失败（Failed to read memory_store.json），将使用空结构：", repr(e))

    return {
        "conversation_summaries": [],
    }


def save_memory_store(data: Dict[str, Any]) -> None:
    """写回 memory_store.json。Write updated data back to memory_store.json."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 已写入 memory_store.json（saved to memory_store.json） -> {MEMORY_FILE}")


# ========== 从 events 中抽 compacted_content 的工具 / Extraction helpers ==========

def _safe_get_actions(ev: Any) -> Optional[Dict[str, Any]]:
    """
    兼容不同 ADK 版本下 event.actions / event.data['actions'] 结构。
    Compatible with different ADK versions: handle both event.actions and event.data['actions'].
    """
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
    """
    从 session.events 中抽取 compaction summary 记录，结构：
    Extract compaction summary records from session.events in the structure below:

    {
        "app_name": ...,
        "user_id": ...,
        "session_id": ...,
        "created_at": ... (ISO8601),
        "summary_text": ...,
        "raw": { ... 或 repr(compacted_content) ... } / raw serialized compacted_content
    }
    """
    records: List[Dict[str, Any]] = []

    app_name = getattr(session, "app_name", APP_NAME)
    user_id = getattr(session, "user_id", USER_ID)

    for ev in session.events:
        actions = _safe_get_actions(ev)
        if not actions:
            continue

        compaction = actions.get("compaction") if isinstance(actions, dict) else None
        if not compaction:
            continue

        # 对象转 dict / convert object-like compaction to dict
        if not isinstance(compaction, dict) and hasattr(compaction, "__dict__"):
            compaction = compaction.__dict__

        compacted = None
        if isinstance(compaction, dict):
            compacted = compaction.get("compacted_content")

        if not compacted:
            continue

        summary_text: str

        # ---- A) 纯字符串 / plain string ----
        if isinstance(compacted, str):
            summary_text = compacted
            raw_struct: Any = {"text": compacted}

        # ---- B) Content-like 对象（例如有 .parts[0].text）/ Content-like object (e.g., .parts[0].text) ----
        elif hasattr(compacted, "parts"):
            try:
                parts = getattr(compacted, "parts", None)
                text_candidate = None
                if parts and len(parts) > 0:
                    first = parts[0]
                    # google.genai.types.Part(text=...)
                    text_candidate = getattr(first, "text", None)
                summary_text = text_candidate or str(compacted)
            except Exception:
                summary_text = str(compacted)
            raw_struct = {"repr": str(compacted)}

        # ---- C) dict 结构（有可能是 content dict）/ dict structure (maybe a content dict) ----
        elif isinstance(compacted, dict):
            parts = compacted.get("parts")
            text_candidate = None
            if isinstance(parts, list) and parts:
                first = parts[0]
                if isinstance(first, dict) and "text" in first:
                    text_candidate = first["text"]

            summary_text = (
                text_candidate
                or compacted.get("text")
                or json.dumps(compacted, ensure_ascii=False)
            )
            raw_struct = compacted

        # ---- D) 兜底 / fallback ----
        else:
            summary_text = str(compacted)
            raw_struct = {"value": summary_text}

        # ---- 时间戳归一化：统一成 ISO8601 / normalize timestamp to ISO8601 ----
        ts = getattr(ev, "timestamp", None) or getattr(ev, "create_time", None)
        if isinstance(ts, (int, float)):
            created_at = datetime.utcfromtimestamp(ts).isoformat() + "Z"
        else:
            created_at = ts or datetime.utcnow().isoformat() + "Z"

        # ---- session_id：保证有值 / ensure session_id exists ----
        session_id = getattr(ev, "session_id", None) or getattr(ev, "session", None) or getattr(
            session, "id", None
        )

        record = {
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
            "created_at": created_at,
            "summary_text": summary_text,
            "raw": raw_struct,
        }
        records.append(record)

    return records


def append_compaction_records_to_memory(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """把 compaction 记录追加到 memory_store.json 的 conversation_summaries 中。Append compaction records into memory_store.json under conversation_summaries."""
    memory = load_memory_store()
    conv_summaries: List[Dict[str, Any]] = memory.setdefault(
        "conversation_summaries", []
    )

    for r in records:
        print("\n📝 抽取到一条 compaction 摘要（Extracted one compaction summary）：")
        print(f"   session_id: {r['session_id']}  # 会话 ID / Session ID")
        print(f"   created_at: {r['created_at']}  # 创建时间 / Created at")
        print(f"   summary_text: {r['summary_text'][:120]}...  # 摘要文本 / Summary preview")

        conv_summaries.append(r)

    save_memory_store(memory)
    return memory


# ========== 对话发送工具（沿用你 Day3 风格） / Dialogue helper ==========

async def send_one(runner: InMemoryRunner, session_id: str, query: str):
    """单轮对话：打印 user / model。Single turn: print user and model messages."""
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


# ========== 主函数 / Main entry ==========

async def main():
    print("🚀 compacted_memory_etl_demo: main() 开始执行 / starting execution")

    # Step 1：Agent（根 Agent / root agent）
    agent = LlmAgent(
        model=Gemini(model=MODEL_NAME),
        name="compaction_memory_agent",
        description="Agent with compaction enabled; summaries will be extracted into long-term memory.",
        tools=[],  # 本项目不需要额外工具 / No extra tools needed here
    )
    print("✅ Agent 创建完成：compaction_memory_agent / Agent created")

    # Step 2：App + EventsCompactionConfig（创建带压缩的应用 / build app with compaction）
    app = App(
        name=APP_NAME,
        root_agent=agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=3,  # 每 3 个 invocation 触发一次压缩 / trigger every 3 invocations
            overlap_size=1,         # 保留最近 1 次 / keep the most recent turn
        ),
    )
    print("✅ App 创建完成（已启用 EventsCompactionConfig）/ App created with EventsCompactionConfig enabled")

    # Step 3：InMemoryRunner（基于 App / based on the App）
    runner = InMemoryRunner(app=app)
    print("✅ InMemoryRunner 创建完成 / InMemoryRunner created")

    # Step 4：创建 session / create session
    session_id = "compacted-memory-etl-demo"
    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    print(f"🆕 新建 session: {session.id}  # 新建会话 / New session created")

    # Step 5：多轮对话，触发 compaction / multi-turn dialogue to trigger compaction
    print("\n🔄 发送多轮关于 AI in healthcare 的问题，以触发 Compaction / sending multiple healthcare questions to trigger compaction")
    queries = [
        "Explain how AI is used in healthcare.",
        "What are some important applications of AI in medical imaging and diagnostics?",
        "How can AI help in drug discovery and personalized treatment?",
        "What are the main risks and challenges of using AI in hospitals?",
        "Please summarize the key opportunities and risks of AI in healthcare.",
    ]

    for q in queries:
        await send_one(runner, session.id, q)

    # Step 6：Dump session.events（摘要打印 / preview summaries）
    print("\n📦 Dump Session Events（摘要预览 / summary preview）")
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

    # Step 7：从 events 中抽 compaction.summary → 写入 memory_store.json
    print("\n🔍 从 Session.events 中抽取 compaction.summary ... / extracting compaction.summary from Session.events ...")
    records = extract_compaction_records_from_session(session)

    if not records:
        print("⚠️ 未发现任何 compaction 摘要记录。（No compaction summary records found.）")
        print("   你可以： / You can:")
        print("   1）降低 compaction_interval； / reduce compaction_interval;")
        print("   2）增加对话轮数； / increase the number of dialogue turns;")
        print("   3）对比 P15 事件结构，微调 extract_compaction_records_from_session 中的字段访问。/ compare with P15 event schema and adjust field access.")
    else:
        memory = append_compaction_records_to_memory(records)

        print("\n📚 当前 memory_store.json 内容（截断预览 / truncated preview）：")
        preview = json.dumps(memory, ensure_ascii=False, indent=2)
        print(preview[:1000], "...\n")

    print("🏁 compacted_memory_etl_demo: main() 执行结束 / execution finished")


if __name__ == "__main__":
    print("👉 通过 __main__ 入口运行 compacted_memory_etl_demo / running via __main__")
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ 程序异常（Program error）:", repr(e))
