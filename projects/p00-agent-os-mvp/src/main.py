# projects/p00-agent-os-mvp/src/main.py
from __future__ import annotations
from typing import Any, Dict
from datetime import datetime, timezone

from adk_runtime import memory_store as legacy_memory_store
from adk_runtime.event_ledger import EventLedger
from adk_runtime.memory_gate_p08 import P08MemoryGate, RuntimeSchema
from adk_runtime.process.boot import boot
from adk_runtime.persona_engine import load_persona
from adk_runtime.observability import log_event, new_trace_id
from adk_runtime.paths import RUNTIME_DATA_DIR, ensure_runtime_dirs
from adk_runtime.trace_context import TraceContext

import uuid





PROJECT_NAME = "p00-agent-os-mvp"
SOURCE_TAG = PROJECT_NAME


def run_with_kernel(
    user_message: str,
    persona: Dict[str, Any],
    memory: Dict[str, Any],
    session_id: str,
    trace_id: str,
) -> Dict[str, Any]:
    """
    这里是对 Google ADK / Kernel 层的“适配函数”。

    在 MVP 阶段可以先用“回声 + 假装工具调用”的方式站住结构，
    后面再逐步替换成真实的 ADK Agent 调用。

    约定输出结构：
    {
      "reply": "... LLM 给用户的文本 ...",
      "tool_calls": [...],   # 可选，记录调用了哪些 Tool
      "debug": {...}         # 可选，内部调试信息
    }
    """
    # TODO: 用你的 ADK 代码替代这一段。
    # 这里先用最小 stub 保证 OS 流程成立。
    reply_text = f"[MVP Kernel Stub] You said: {user_message}"

    # 模拟：agent 决定调用一个 tool
    tool_calls = [
        {
            "tool_name": "fake_search",
            "args": {"q": "AI news this week"},
        }
    ]

    return {
        "reply": reply_text,
        "tool_calls": tool_calls,
        "debug": {
            "kernel": "stub",
            "session_id": session_id,
            "trace_id": trace_id,
        },
    }


def main() -> None:
    ensure_runtime_dirs()
    ledger = EventLedger(RUNTIME_DATA_DIR / "events.jsonl")
    boot_ctx = boot(ledger=ledger)
    ledger = EventLedger(RUNTIME_DATA_DIR / "memory_gate_ledger.jsonl")
    runtime_schema = RuntimeSchema(supported_schema_version=1, supported_store_version=0)
    memory_gate = P08MemoryGate(legacy_memory_store, ledger, runtime_schema)

    session_id = f"p00-{uuid.uuid4()}"
    trace_id = new_trace_id()

    ctx = TraceContext(trace_id=trace_id)

    # P08 startup confrontation (refuse over silent compatibility)
    memory_gate.startup_confrontation(session_id="p00-startup")

    # 1) persona & memory
    persona = load_persona(user_id="susan")
    memory = memory_gate.load_memory()

    root_span_id, _ = ctx.new_span()
    log_event(
        event_type="session.start",
        source=SOURCE_TAG,
        payload={
            "message": "Session started for p00 MVP",
            "persona_user_id": persona.get("user_id"),
        },
        session_id=session_id,
        trace_id=trace_id,
        actor="runtime",
        span_id=root_span_id,
        parent_span_id=None,
    )
    

    user_message = "Hello, this is the first OS-level MVP run."
    user_span_id, _ = ctx.new_span()
    log_event(
        event_type="user.message",
        source=SOURCE_TAG,
        payload={"text": user_message},
        session_id=session_id,
        trace_id=trace_id,
        actor="user",
        span_id=user_span_id,
        parent_span_id=root_span_id,
    )

    kernel_result = run_with_kernel(
        user_message=user_message,
        persona=persona,
        memory=memory,
        session_id=session_id,
        trace_id=trace_id,
    )

    agent_span_id, _ = ctx.new_span()
    log_event(
        event_type="agent.reply",
        source=SOURCE_TAG,
        payload={
            "reply": kernel_result.get("reply"),
            "tool_calls": kernel_result.get("tool_calls", []),
        },
        session_id=session_id,
        trace_id=trace_id,
        actor="agent",
        span_id=agent_span_id,
        parent_span_id=user_span_id,
    )

    for call in kernel_result.get("tool_calls", []):
        tool_span_id, _ = ctx.new_span()
        log_event(
            event_type="tool.call",
            source=SOURCE_TAG,
            payload={
                "tool_name": call.get("tool_name"),
                "args": call.get("args", {}),
            },
            session_id=session_id,
            trace_id=trace_id,
            actor="tool",
            span_id=tool_span_id,
            parent_span_id=agent_span_id,
        )

        tool_output = {"ok": True, "data": "stub tool result"}

        tool_result_span_id, _ = ctx.new_span()
        log_event(
            event_type="tool.result",
            source=SOURCE_TAG,
            payload={
                "tool_name": call.get("tool_name"),
                "result": tool_output,
            },
            session_id=session_id,
            trace_id=trace_id,
            actor="tool",
            span_id=tool_result_span_id,
            parent_span_id=tool_span_id,
        )

    # memory update (P07 allow-list: notes.* only)
    persona_id = persona.get("user_id", "unknown")
    result = memory_gate.save_memory(
        {},
        source="p00",
        actor={"agent_id": "p00", "persona_id": persona_id},
        # All new writes must use runtime.current schema_version; legacy versions are migration-only.
        schema_version=runtime_schema.supported_schema_version,
        zone="observation",
        key=f"notes.session_{session_id}",
        value={
            "text": user_message,
            "ts": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
        },
    )
    if result["status"] == "blocked":
        print("WARNING: Memory write blocked by policy:", result["decision"]["reason"])

    end_span_id, _ = ctx.new_span()
    log_event(
        event_type="session.end",
        source=SOURCE_TAG,
        payload={"message": "Session ended for p00 MVP"},
        session_id=session_id,
        trace_id=trace_id,
        actor="runtime",
        span_id=end_span_id,
        parent_span_id=root_span_id,
    )

    print(kernel_result["reply"])
    # P10: emit system.shutdown for this run (Event Envelope v1)
    shutdown_span = str(uuid.uuid4())
    from adk_runtime.events import append_event
    append_event(
        event_type="system.shutdown",
        session_id="system",
        trace_id=boot_ctx.run_id,
        payload={
            "system_id": boot_ctx.system_id,
            "process_id": boot_ctx.process_id,
            "run_id": boot_ctx.run_id,
            "exit_reason": "normal",
            "_actor": "runtime",
            "_source": SOURCE_TAG,
            "_span_id": shutdown_span,
        },
    )



if __name__ == "__main__":
    main()
