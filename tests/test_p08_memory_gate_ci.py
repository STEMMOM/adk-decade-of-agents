from __future__ import annotations

from datetime import datetime, timezone
import uuid

from adk_runtime import memory_store as legacy_memory_store
from adk_runtime.event_ledger import EventLedger
from adk_runtime.memory_gate_p08 import P08MemoryGate, RuntimeSchema
from adk_runtime.paths import RUNTIME_DATA_DIR, ensure_runtime_dirs


def _utc_ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def test_p08_allows_current_schema_write_and_blocks_missing_schema_version():
    """
    P08 constitutional regression:
    - current schema write must commit
    - missing schema_version must block with UC-01
    """
    ensure_runtime_dirs()

    ledger_path = RUNTIME_DATA_DIR / f"ci_memory_gate_ledger_{uuid.uuid4().hex}.jsonl"
    ledger = EventLedger(ledger_path)

    runtime_schema = RuntimeSchema(supported_schema_version=1, supported_store_version=0)
    gate = P08MemoryGate(legacy_memory_store, ledger, runtime_schema)

    gate.startup_confrontation(session_id=f"ci-startup-{uuid.uuid4().hex}")

    committed = gate.save_memory(
        {},
        source="ci",
        actor={"agent_id": "ci", "persona_id": "test"},
        schema_version=runtime_schema.supported_schema_version,
        zone="observation",
        key="observations.ci_smoke",
        value={"ts": _utc_ts(), "note": "ci constitutional test"},
    )
    assert committed["status"] == "committed", committed

    blocked = gate.save_memory(
        {},
        source="ci",
        actor={"agent_id": "ci", "persona_id": "test"},
        zone="observation",
        key="observations.ci_missing_schema",
        value={"ts": _utc_ts()},
    )
    assert blocked["status"] == "blocked", blocked
    assert blocked["decision"]["reason"] == "UC-01: missing schema_version", blocked
