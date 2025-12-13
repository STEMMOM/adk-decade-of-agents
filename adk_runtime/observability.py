# adk_runtime/observability.py
from __future__ import annotations
import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from .paths import EVENTS_FILE, ensure_runtime_dirs, get_log_file


@dataclass
class Event:
    """
    event_protocol_v1 — MVP 结构
    
    必备字段：
    - event_type: 语义类别，例如 "session.start" / "agent.tool_call"
    - source: 事件来源模块或项目，例如 "p00-agent-os-mvp"
    - payload: 事件具体内容（任意 JSON）
    - timestamp: ISO 风格字符串（这里简化为秒级）
    - session_id: 当前会话 id（字符串）
    - trace_id: 用于关联同一条执行链
    """
    event_type: str
    source: str
    payload: Dict[str, Any]
    timestamp: str
    session_id: str
    trace_id: str


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_trace_id() -> str:
    return str(uuid.uuid4())


def log_event(
    event_type: str,
    source: str,
    payload: Dict[str, Any],
    session_id: str,
    trace_id: str,
) -> None:
    """以 JSONL 形式把事件写入 OS 级 events.jsonl。"""
    ensure_runtime_dirs()
    event = Event(
        event_type=event_type,
        source=source,
        payload=payload,
        timestamp=_now_iso(),
        session_id=session_id,
        trace_id=trace_id,
    )
    line = json.dumps(asdict(event), ensure_ascii=False)
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

    # 同时写一份人类可读日志（MVP）
    log_file = get_log_file()
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{event.timestamp}] {event_type} ({source}) {payload}\n")
