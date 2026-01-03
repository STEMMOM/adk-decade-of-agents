from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from adk_runtime.events import append_event

@dataclass
class EventLedger:
    path: Path

    def __post_init__(self) -> None:
        self.path = self.path if isinstance(self.path, Path) else Path(self.path)

    def append(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        ts: Optional[str] = None,
    ) -> None:
        payload = dict(payload) if payload else {}
        # derive session_id
        sid = session_id or payload.pop("session_id", None) or "unknown"
        # derive trace_id, remove from payload
        trace = trace_id or payload.pop("trace_id", None) or payload.pop("_trace_id", None) or "unknown"
        # ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        append_event(
            event_type=event_type,
            session_id=sid,
            trace_id=trace,
            payload=payload,
            ts=ts,
        )

    def read_all(self) -> list[dict]:
        """
        Read all events (oldest -> newest). Return [] if file missing.
        Raise ValueError on invalid JSON with file path and line number.
        """
        p = self.path if isinstance(self.path, Path) else Path(self.path)
        if not p.exists():
            return []
        events = []
        with p.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception as exc:
                    raise ValueError(f"Invalid JSON in {p} at line {idx}") from exc
        return events
