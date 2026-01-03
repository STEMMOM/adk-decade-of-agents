from __future__ import annotations

import json
from pathlib import Path

import pytest


EVENTS_PATH = Path("runtime_data/events.jsonl")


def _load_events() -> list[dict]:
    if not EVENTS_PATH.exists():
        pytest.skip(f"missing ledger: {EVENTS_PATH}")
    events: list[dict] = []
    with EVENTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def test_run_level_invariants():
    events = _load_events()
    boots = [e for e in events if e.get("event_type") == "system.boot"]
    shutdowns = [e for e in events if e.get("event_type") == "system.shutdown"]

    # 1) Each run_id SHOULD have exactly one system.boot
    boot_counts: dict[str, int] = {}
    for ev in boots:
        rid = (ev.get("payload") or {}).get("run_id")
        if not isinstance(rid, str):
            continue
        boot_counts[rid] = boot_counts.get(rid, 0) + 1
    assert all(count == 1 for count in boot_counts.values()), f"boot count violation: {boot_counts}"

    # 2) Each run_id MUST have at most one system.shutdown
    shutdown_counts: dict[str, int] = {}
    for ev in shutdowns:
        rid = (ev.get("payload") or {}).get("run_id")
        if not isinstance(rid, str):
            continue
        shutdown_counts[rid] = shutdown_counts.get(rid, 0) + 1
    assert all(count <= 1 for count in shutdown_counts.values()), f"shutdown count violation: {shutdown_counts}"

    # 3) If a run has boot but no shutdown, next boot for same system_id MUST be recover, SHOULD reference recovered_from_run_id
    # Interpret "next boot" by JSONL order.
    last_boot_by_system: dict[str, dict] = {}
    shutdown_seen: set[tuple[str, str]] = set()  # (system_id, run_id)
    for ev in events:
        et = ev.get("event_type")
        payload = ev.get("payload") or {}
        sys_id = payload.get("system_id")
        run_id = payload.get("run_id")
        if et == "system.boot":
            prior = last_boot_by_system.get(sys_id)
            if prior and (sys_id, prior.get("run_id")) not in shutdown_seen:
                # must be recover
                assert payload.get("boot_mode") == "recover", f"recover required for system {sys_id}"
                assert payload.get("recovered_from_run_id") == prior.get("run_id"), "recovered_from_run_id should reference prior run"
            last_boot_by_system[sys_id] = payload
        elif et == "system.shutdown":
            if sys_id and run_id:
                shutdown_seen.add((sys_id, run_id))


def test_synthetic_closure_invariants():
    """
    Synthetic run created in-memory must have exactly one shutdown.
    """
    run_id = "run_synth_001"
    sys_id = "sys_synth"
    proc_id = "proc_synth"
    synth_events = [
        {
            "event_type": "system.boot",
            "payload": {"system_id": sys_id, "process_id": proc_id, "run_id": run_id},
        },
        {
            "event_type": "system.shutdown",
            "payload": {"system_id": sys_id, "process_id": proc_id, "run_id": run_id},
        },
    ]
    boots = [e for e in synth_events if e["event_type"] == "system.boot"]
    shutdowns = [e for e in synth_events if e["event_type"] == "system.shutdown"]
    assert len(boots) == 1
    assert len(shutdowns) == 1
