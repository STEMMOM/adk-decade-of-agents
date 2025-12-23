from __future__ import annotations

from typing import Optional

from adk_runtime.event_ledger import EventLedger
from adk_runtime.process.boot import BootContext


def shutdown(
    *,
    ledger: EventLedger,
    ctx: BootContext,
    exit_reason: str = "normal",
    session_id: Optional[str] = None,
) -> None:
    ledger.append(
        "system.shutdown",
        {
            "system_id": ctx.system_id,
            "process_id": ctx.process_id,
            "run_id": ctx.run_id,
            "exit_reason": exit_reason,
        },
        session_id=session_id,
    )
