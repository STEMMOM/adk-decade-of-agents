from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on PYTHONPATH so `import adk_runtime` works.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adk_runtime import paths
from adk_runtime.event_ledger import EventLedger
from adk_runtime.process import boot
from adk_runtime.process.lifecycle import shutdown


def main():
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
