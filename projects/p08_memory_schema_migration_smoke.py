from __future__ import annotations

from datetime import datetime, timezone

from adk_runtime import memory_store as legacy_memory_store
from adk_runtime.event_ledger import EventLedger
from adk_runtime.memory_gate_p08 import P08MemoryGate, RuntimeSchema
from adk_runtime.paths import RUNTIME_DATA_DIR, ensure_runtime_dirs


def run_smoke():
    ensure_runtime_dirs()
    ledger = EventLedger(RUNTIME_DATA_DIR / "memory_gate_ledger_smoke.jsonl")
    runtime_schema = RuntimeSchema(supported_schema_version=1, supported_store_version=0)
    gate = P08MemoryGate(legacy_memory_store, ledger, runtime_schema)

    gate.startup_confrontation(session_id="smoke-startup")

    ok = gate.save_memory(
        {},
        source="smoke",
        actor={"agent_id": "smoke", "persona_id": "test"},
        # All new writes must use runtime.current schema_version; legacy versions are migration-only.
        schema_version=runtime_schema.supported_schema_version,
        zone="observation",
        key="observations.smoke_test",
        value={
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "note": "smoke test",
        },
    )
    print("observation write:", ok)

    blocked = gate.save_memory(
        {},
        source="smoke",
        actor={"agent_id": "smoke", "persona_id": "test"},
        zone="observation",
        key="observations.missing_schema",
        value={"ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")},
    )
    print("missing schema_version:", blocked)


if __name__ == "__main__":
    run_smoke()
