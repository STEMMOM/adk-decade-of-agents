from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class EventLedger:
    path: Path

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
