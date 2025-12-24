from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Literal, Dict, Any

from adk_runtime import paths
from adk_runtime.event_ledger import EventLedger
from adk_runtime import trace_context


BootMode = Literal["cold", "warm", "recover"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class BootContext:
    system_id: str
    process_id: str
    run_id: str
    boot_mode: BootMode
    started_at: str
    recovered_from_run_id: Optional[str] = None


def _system_identity_path() -> str:
    # Keep this separate from memory_store schema on purpose.
    return os.path.join(paths.runtime_data_dir(), "system_identity.json")


def load_or_create_system_id() -> Dict[str, Any]:
    p = _system_identity_path()
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "system_id" not in data or not data["system_id"]:
            raise ValueError("system_identity.json exists but system_id missing")
        return data

    data = {
        "schema_version": 1,
        "system_id": f"sys_{uuid.uuid4().hex}",
        "created_at": _utc_now_iso(),
    }
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def _get_last_run_status(ledger: EventLedger) -> Dict[str, Any]:
    """
    Minimal recovery detection:
    - Find last system.boot, and check whether a matching system.shutdown exists.
    - If last boot exists but shutdown missing => recover
    - Else warm (if store exists) / cold (if store missing)
    """
    # We rely on ledger's ability to read events. If you don't have it yet,
    # implement a minimal read in EventLedger (or read events.jsonl directly here).
    events = ledger.read_all()  # expected: list of dict events (oldest -> newest)
    last_boot = None
    last_shutdown_by_run: Dict[str, Dict[str, Any]] = {}

    for ev in events:
        et = ev.get("event_type") or ev.get("type")
        payload = ev.get("payload") or {}
        rid = payload.get("run_id") or ev.get("run_id")
        if et == "system.boot":
            last_boot = ev
        elif et == "system.shutdown":
            if rid:
                last_shutdown_by_run[rid] = ev

    if not last_boot:
        return {"status": "no_boot_found"}

    last_boot_payload = last_boot.get("payload") or {}
    rid = last_boot_payload.get("run_id") or last_boot.get("run_id")
    if rid and rid not in last_shutdown_by_run:
        return {
            "status": "incomplete",
            "recovered_from_run_id": rid,
        }

    return {
        "status": "complete",
        "last_run_id": rid,
    }


def boot(*, ledger: EventLedger) -> BootContext:
    identity = load_or_create_system_id()
    system_id = identity["system_id"]

    process_id = f"proc_{uuid.uuid4().hex}"
    run_id = f"run_{uuid.uuid4().hex}"
    started_at = _utc_now_iso()

    # Determine boot_mode using observable artifacts
    memory_store_path = paths.memory_store_path()
    has_store = os.path.exists(memory_store_path)

    recovered_from: Optional[str] = None
    if not has_store:
        boot_mode: BootMode = "cold"
    else:
        last_status = _get_last_run_status(ledger)
        if last_status.get("status") == "incomplete":
            boot_mode = "recover"
            recovered_from = last_status.get("recovered_from_run_id")
        else:
            boot_mode = "warm"

    ctx = BootContext(
        system_id=system_id,
        process_id=process_id,
        run_id=run_id,
        boot_mode=boot_mode,
        started_at=started_at,
        recovered_from_run_id=recovered_from,
    )

    # Set context before any downstream observability writes.
    trace_context.set_process_context(ctx.system_id, ctx.process_id, ctx.run_id)

    # Write system.boot as an auditable fact
    ledger.append(
        "system.boot",
        {
            "system_id": ctx.system_id,
            "process_id": ctx.process_id,
            "run_id": ctx.run_id,
            "boot_mode": ctx.boot_mode,
            "started_at": ctx.started_at,
            "recovered_from_run_id": ctx.recovered_from_run_id,
        },
    )

    return ctx
