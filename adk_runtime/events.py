from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .paths import EVENTS_FILE, ensure_runtime_dirs
from adk_runtime.trace_context import get_current_actor

SCHEMA_VERSION = "1.1"


def utc_ts_iso() -> str:
    # UTC, RFC3339-ish with milliseconds, always ends with Z
    dt = datetime.now(timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_json(obj: Any) -> str:
    """
    Deterministic JSON string:
    - sort keys
    - no whitespace
    - ensure_ascii=False (stable for unicode)
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EventEnvelopeV1:
    schema_version: str
    event_type: str
    session_id: str
    trace_id: str
    ts: str
    payload: Dict[str, Any]
    payload_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "ts": self.ts,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
        }


class EventWriter:
    """
    Single write入口：所有事件都从这里 append 到 events.jsonl
    """
    def __init__(self, events_file: Path):
        self.events_file = events_file
        self.events_file.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        *,
        event_type: str,
        session_id: str,
        trace_id: str,
        payload: Optional[Dict[str, Any]] = None,
        ts: Optional[str] = None,
        actor: Optional[Dict[str, Any]] = None,
    ) -> EventEnvelopeV1:
        payload = payload or {}
        # Normalize reserved meta-fields inside payload; remove forbidden/legacy keys.
        if "trace_id" in payload:
            payload = dict(payload)
            payload.pop("trace_id", None)
        # migrate legacy span keys if reserved not set
        for legacy, reserved in (("span_id", "_span_id"), ("parent_span_id", "_parent_span_id")):
            if legacy in payload and reserved not in payload:
                payload = dict(payload)
                payload[reserved] = payload.pop(legacy)
            elif legacy in payload:
                payload = dict(payload)
                payload.pop(legacy, None)
        ts = ts or utc_ts_iso()

        act = actor if actor is not None else get_current_actor()
        assert isinstance(act, dict), "actor must be a dict"
        assert act.get("kind"), "actor.kind required"
        assert act.get("id"), "actor.id required"
        assert act.get("id") != "unknown", "actor.id must not be unknown"

        payload_canon = canonical_json(payload)
        payload_hash = sha256_hex(payload_canon)

        env = EventEnvelopeV1(
            schema_version=SCHEMA_VERSION,
            event_type=event_type,
            session_id=session_id,
            trace_id=trace_id,
            ts=ts,
            payload=payload,
            payload_hash=payload_hash,
        )

        env_dict = env.to_dict()
        env_dict["actor"] = act
        line = canonical_json(env_dict)
        with self.events_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

        return env


def append_event(
    *,
    event_type: str,
    session_id: str,
    trace_id: str,
    payload: Optional[Dict[str, Any]] = None,
    ts: Optional[str] = None,
    actor: Optional[Dict[str, Any]] = None,
) -> EventEnvelopeV1:
    ensure_runtime_dirs()
    writer = EventWriter(EVENTS_FILE)
    return writer.emit(
        event_type=event_type,
        session_id=session_id,
        trace_id=trace_id,
        payload=payload,
        ts=ts,
        actor=actor,
    )
