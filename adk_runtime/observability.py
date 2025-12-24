# adk_runtime/observability.py
from __future__ import annotations
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .paths import EVENTS_FILE, RUNTIME_DATA_DIR, ensure_runtime_dirs, get_log_file
from .events import EventWriter  # ✅ P04：统一信封写入口
from . import trace_context


# P09: canonical observability ledger (append-only, replayable)
OBS_DIR = RUNTIME_DATA_DIR / "observability"
OBS_EVENTS_FILE = OBS_DIR / "observability_events.jsonl"


def _iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _now_human() -> str:
    # 给人类日志用（秒级足够）
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_trace_id() -> str:
    return str(uuid.uuid4())


def _require_run_id(run_id: str, event_type: str) -> str:
    """P09 v1.1: run_id must be present and non-empty."""
    if run_id is None:
        raise ValueError(f"run_id is required for event_type={event_type}")
    if isinstance(run_id, str) and run_id.strip():
        return run_id
    raise ValueError(f"run_id must be non-empty for event_type={event_type}")


def _normalize_layer(event_type: str, layer: Optional[str]) -> str:
    """P09 v1.1: minimal layer mapping."""
    if layer:
        return layer
    if event_type.startswith("tool."):
        return "tool"
    if event_type.startswith("policy."):
        return "policy"
    if event_type.startswith("memory."):
        return "memory"
    if event_type.startswith("ir."):
        return "ir"
    return "runtime"


def emit_event(
    event_type: str,
    run_id: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
    layer: Optional[str] = None,
    timestamp: Optional[str] = None,
    latency_ms: Optional[int] = None,
    session_id: Optional[str] = None,
    system_id: Optional[str] = None,
    process_id: Optional[str] = None,
) -> None:
    """P09: append-only event emission with canonical fields. P09 v1.1 adds run_id enforcement, layer normalization, latency_ms top-level."""
    ensure_runtime_dirs()
    OBS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = _require_run_id(run_id, event_type)
    norm_layer = _normalize_layer(event_type, layer)
    record = {
        "event_type": event_type,
        "run_id": run_id,
        "timestamp": timestamp or _iso_utc(),
    }
    if system_id:
        record["system_id"] = system_id
    if process_id:
        record["process_id"] = process_id
    if norm_layer:
        record["layer"] = norm_layer
    if latency_ms is not None:
        record["latency_ms"] = int(latency_ms)
    if session_id:
        record["session_id"] = session_id
    if payload:
        # optional backward-compatible copy
        if latency_ms is not None:
            payload = dict(payload)
            payload.setdefault("latency_ms", latency_ms)
        record["payload"] = payload
    line = json.dumps(record, ensure_ascii=False)
    with OBS_EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def span_start(event_type: str, run_id: str, *, layer: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Start a span; returns a token for finish with monotonic start time."""
    start_ts = _iso_utc()
    start_perf = time.perf_counter()
    emit_event(event_type, run_id, payload=payload, layer=layer, timestamp=start_ts)
    return {"event_type": event_type, "run_id": run_id, "layer": layer, "start_perf": start_perf}


def span_finish(
    span_token: Dict[str, Any],
    finished_event_type: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Finish a span; emits finished event with latency_ms."""
    latency_ms = int((time.perf_counter() - span_token["start_perf"]) * 1000)
    emit_event(
        finished_event_type,
        span_token["run_id"],
        payload=payload,
        layer=span_token.get("layer"),
        latency_ms=latency_ms,
    )


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
    layer: Optional[str] = None,
) -> None:
    """
    Existing interface retained; now emits P09-compliant observability events (run_id=session_id).
    """
    ensure_runtime_dirs()

    p = dict(payload)
    p["_source"] = source
    p["_trace_id"] = trace_id
    system_id = trace_context.get_system_id()
    process_id = trace_context.get_process_id()
    run_id = trace_context.get_run_id()
    if system_id:
        p["_system_id"] = system_id
    if process_id:
        p["_process_id"] = process_id
    if not run_id:
        run_id = "unknown"
        p["_missing_run_id_reason"] = "no_trace_context"

    if actor is not None:
        p["_actor"] = actor
    if span_id is not None:
        p["_span_id"] = span_id
    if parent_span_id is not None:
        p["_parent_span_id"] = parent_span_id

    emit_event(
        event_type=event_type,
        run_id=run_id,
        payload=p,
        layer=_normalize_layer(event_type, layer),
        session_id=session_id,
        system_id=system_id,
        process_id=process_id,
    )

    # ✅ 同时写一份人类可读日志（MVP 保留）
    log_file = get_log_file()
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{_now_human()}] {event_type} ({source}) {payload}\n")
