from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from adk_runtime import paths
from adk_runtime.event_ledger import EventLedger
from adk_runtime.process import boot

ledger = EventLedger(path=str(paths.events_ledger_path()))
ctx = boot(ledger=ledger)
print(f"[P10-crash] wrote boot only run_id={ctx.run_id}")
raise RuntimeError("intentional crash before shutdown")
