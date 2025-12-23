from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class EventLedger:
    path: Path

    def __post_init__(self) -> None:
        self.path = self.path if isinstance(self.path, Path) else Path(self.path)

    def append(self, event_type: str, payload: Dict[str, Any], *, session_id: Optional[str] = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": time.time(),
            "event_type": event_type,
            "session_id": session_id,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

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
