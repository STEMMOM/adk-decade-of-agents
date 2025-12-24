from __future__ import annotations

import sys
import json
from pathlib import Path

# Ensure repo root is on PYTHONPATH so `import adk_runtime` works.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adk_runtime import paths
from adk_runtime.event_ledger import EventLedger
from adk_runtime.process import boot
from adk_runtime.process.lifecycle import shutdown

def _detect_unclosed_run(events_path: Path) -> str | None:
    if not events_path.exists():
        return None
    boots: list[str] = []
    shutdowns: set[str] = set()
    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            et = ev.get("event_type")
            payload = ev.get("payload") or {}
            rid = payload.get("run_id") or ev.get("run_id")
            if not rid:
                continue
            if et == "system.boot":
                boots.append(rid)
            elif et == "system.shutdown":
                shutdowns.add(rid)
    for rid in reversed(boots):
        if rid not in shutdowns:
            return rid
    return None


def main():
    # Detect prior unclosed run to enable recover boot_mode.
    events_path = paths.events_ledger_path()
    unclosed = _detect_unclosed_run(events_path)
    if unclosed:
        mpath = paths.memory_store_path()
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.touch(exist_ok=True)

    ledger = EventLedger(path=paths.events_ledger_path())
    try:
        ctx = boot(ledger=ledger)
        print(f"[P10] boot_mode={ctx.boot_mode} system_id={ctx.system_id} run_id={ctx.run_id}")
    except Exception:
        shutdown(ledger=ledger, ctx=ctx, exit_reason="exception")
        raise
    else:
        shutdown(ledger=ledger, ctx=ctx, exit_reason="normal")


if __name__ == "__main__":
    main()
