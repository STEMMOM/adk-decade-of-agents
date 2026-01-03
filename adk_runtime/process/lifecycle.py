from __future__ import annotations

import atexit
import signal
import uuid
from typing import Optional

from adk_runtime.event_ledger import EventLedger
from adk_runtime.process.boot import BootContext
from adk_runtime import trace_context
from adk_runtime.events import append_event


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


def install_lifecycle_hooks(ctx: BootContext, source: str) -> None:
    emitted: dict[str, bool] = {"done": False}

    def _emit_shutdown(reason: str) -> None:
        if emitted["done"]:
            return
        emitted["done"] = True
        payload = {
            "system_id": ctx.system_id,
            "process_id": ctx.process_id,
            "run_id": ctx.run_id,
            "exit_reason": reason,
            "_actor": "runtime",
            "_source": source,
            "_span_id": str(uuid.uuid4()),
        }
        append_event(
            event_type="system.shutdown",
            session_id="system",
            trace_id=ctx.run_id,
            payload=payload,
        )

    def _atexit() -> None:
        _emit_shutdown("atexit")

    def _handle(signum, frame) -> None:  # type: ignore[no-untyped-def]
        _emit_shutdown(f"signal:{signum}")

    atexit.register(_atexit)
    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)
