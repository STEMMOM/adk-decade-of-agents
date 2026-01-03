import json
import os
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENTS_PATH = REPO_ROOT / "runtime_data" / "events.jsonl"


def _load_events(path: Path):
    if not path.exists():
        pytest.skip(f"events ledger not found: {path}")
    events = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON on line {i}: {e}")
    return events


def _pick_latest_boot(events):
    boots = [e for e in events if e.get("event_type") == "system.boot"]
    if not boots:
        pytest.fail("No system.boot event found in events ledger.")
    # Use ts lexical order (ISO 8601 Z). This is safe for your current format.
    boots.sort(key=lambda e: e.get("ts", ""))
    return boots[-1]


def _find_shutdown_for_trace(events, trace_id):
    # Find the first shutdown after the boot with same trace_id (or the last in ledger).
    shutdowns = [
        e for e in events
        if e.get("event_type") == "system.shutdown" and e.get("trace_id") == trace_id
    ]
    if not shutdowns:
        return None
    shutdowns.sort(key=lambda e: e.get("ts", ""))
    return shutdowns[-1]


def _assert_required_payload_fields(event, fields):
    payload = event.get("payload")
    assert isinstance(payload, dict), f"{event.get('event_type')} payload must be an object"
    for f in fields:
        assert f in payload and payload[f], (
            f"{event.get('event_type')} payload missing required field '{f}'"
        )


def _assert_session_not_unknown(event):
    session_id = event.get("session_id")
    assert session_id is not None and session_id != "unknown", (
        f"{event.get('event_type')} session_id must not be 'unknown' (got: {session_id!r})"
    )


def _assert_trace_equals_run_id(event):
    trace_id = event.get("trace_id")
    payload = event.get("payload") or {}
    run_id = payload.get("run_id")
    assert trace_id and run_id, (
        f"{event.get('event_type')} requires both trace_id and payload.run_id"
    )
    assert trace_id == run_id, (
        f"{event.get('event_type')} trace_id must equal payload.run_id "
        f"(trace_id={trace_id!r}, run_id={run_id!r})"
    )


def _assert_runtime_actor_present(event):
    # P00 minimal: runtime identity must be visible in boot/shutdown payload.
    payload = event.get("payload") or {}
    # Your current boot/shutdown payload uses either 'actor' or '_actor' (or both)
    actor = payload.get("actor") or payload.get("_actor")
    assert actor, f"{event.get('event_type')} payload must include runtime actor ('actor' or '_actor')"


@pytest.mark.institution
def test_p00_boot_invariants():
    # Allow override via env for CI / alternate ledgers.
    events_path = Path(os.environ.get("ADK_EVENTS_PATH", str(DEFAULT_EVENTS_PATH)))
    events = _load_events(events_path)

    boot = _pick_latest_boot(events)
    trace_id = boot.get("trace_id")

    # --- Boot invariants ---
    _assert_session_not_unknown(boot)
    _assert_required_payload_fields(boot, ["system_id", "process_id", "run_id"])
    _assert_trace_equals_run_id(boot)
    _assert_runtime_actor_present(boot)

    # --- Shutdown invariants (same run) ---
    shutdown = _find_shutdown_for_trace(events, trace_id)
    assert shutdown is not None, (
        f"No system.shutdown found for trace_id={trace_id!r}. "
        "A run must form a closed boot→shutdown chain."
    )

    _assert_session_not_unknown(shutdown)
    _assert_required_payload_fields(shutdown, ["system_id", "process_id", "run_id"])
    _assert_trace_equals_run_id(shutdown)
    _assert_runtime_actor_present(shutdown)
