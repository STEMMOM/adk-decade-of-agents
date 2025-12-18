# adk_runtime/observability.py
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, Optional

from .paths import EVENTS_FILE, ensure_runtime_dirs, get_log_file
from .events import EventWriter  # ✅ P04：统一信封写入口


def _now_human() -> str:
    # 给人类日志用（秒级足够）
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_trace_id() -> str:
    return str(uuid.uuid4())


_writer: Optional[EventWriter] = None


def _get_writer() -> EventWriter:
    global _writer
    if _writer is None:
        ensure_runtime_dirs()
        _writer = EventWriter(EVENTS_FILE)
    return _writer


def log_event(
    event_type: str,
    source: str,
    payload: Dict[str, Any],
    session_id: str,
    trace_id: str,
    *,
    actor: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
) -> None:
    ensure_runtime_dirs()

    p = dict(payload)
    p["_source"] = source
    if actor is not None:
        p["_actor"] = actor
    if span_id is not None:
        p["_span_id"] = span_id
    if parent_span_id is not None:
        p["_parent_span_id"] = parent_span_id

    _get_writer().emit(
        event_type=event_type,
        session_id=session_id,
        trace_id=trace_id,
        payload=p,
    )

    # ✅ 同时写一份人类可读日志（MVP 保留）
    log_file = get_log_file()
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{_now_human()}] {event_type} ({source}) {payload}\n")




