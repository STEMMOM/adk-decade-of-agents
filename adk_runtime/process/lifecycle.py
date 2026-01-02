from __future__ import annotations

from typing import Optional

from adk_runtime.event_ledger import EventLedger
from adk_runtime.process.boot import BootContext
from adk_runtime import trace_context
import uuid


def shutdown(
    *,
    ledger: EventLedger,
    ctx: BootContext,
    exit_reason: str = "normal",
    session_id: Optional[str] = None,
) -> None:
    span_id = str(uuid.uuid4())
    parent_span = trace_context.get_boot_span_id()
    payload = {
        "system_id": ctx.system_id,
        "process_id": ctx.process_id,
        "run_id": ctx.run_id,
        "exit_reason": exit_reason,
        "trace_id": ctx.run_id,
        "actor": "runtime",
        "span_id": span_id,
        "_actor": "runtime",
        "_span_id": span_id,
    }
    if parent_span:
        payload["parent_span_id"] = parent_span
        payload["_parent_span_id"] = parent_span
    ledger.append("system.shutdown", payload, session_id=session_id or "system")
