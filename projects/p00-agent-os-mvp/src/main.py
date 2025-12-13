# projects/p00-agent-os-mvp/src/main.py
from __future__ import annotations
from typing import Any, Dict

from adk_runtime.memory_store import load_memory, save_memory
from adk_runtime.persona_engine import load_persona
from adk_runtime.observability import log_event, new_trace_id
from adk_runtime.paths import ensure_runtime_dirs


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

    return {
        "reply": reply_text,
        "tool_calls": [],
        "debug": {
            "kernel": "stub",
            "session_id": session_id,
            "trace_id": trace_id,
        },
    }


def main() -> None:
    ensure_runtime_dirs()

    session_id = "p00-demo-session"
    trace_id = new_trace_id()

    # 1) 加载 OS 级 persona & memory
    persona = load_persona(user_id="susan")
    memory = load_memory()

    log_event(
        event_type="session.start",
        source=SOURCE_TAG,
        payload={
            "message": "Session started for p00 MVP",
            "persona_user_id": persona.get("user_id"),
        },
        session_id=session_id,
        trace_id=trace_id,
    )

    # 2) 模拟一条用户输入（你可以改成 CLI / 参数）
    user_message = "Hello, this is the first OS-level MVP run."
    log_event(
        event_type="user.message",
        source=SOURCE_TAG,
        payload={"text": user_message},
        session_id=session_id,
        trace_id=trace_id,
    )

    # 3) 把 persona + memory 一起喂给 Kernel 层
    kernel_result = run_with_kernel(
        user_message=user_message,
        persona=persona,
        memory=memory,
        session_id=session_id,
        trace_id=trace_id,
    )

    # 4) 记录 Kernel 输出为事件
    log_event(
        event_type="agent.reply",
        source=SOURCE_TAG,
        payload={
            "reply": kernel_result.get("reply"),
            "tool_calls": kernel_result.get("tool_calls", []),
        },
        session_id=session_id,
        trace_id=trace_id,
    )

    # 5) 更新长期记忆（MVP：只是追加一条 summary）
    conversation_summaries = memory.setdefault("conversation_summaries", [])
    conversation_summaries.append(
        {
            "app_name": PROJECT_NAME,
            "session_id": session_id,
            "summary_text": f"MVP run: user said '{user_message}', agent replied stub text.",
            "trace_id": trace_id,
        }
    )
    save_memory(memory)

    log_event(
        event_type="session.end",
        source=SOURCE_TAG,
        payload={"message": "Session ended for p00 MVP"},
        session_id=session_id,
        trace_id=trace_id,
    )

    # 在控制台打印一行，证明一切走完
    print(kernel_result["reply"])


if __name__ == "__main__":
    main()
