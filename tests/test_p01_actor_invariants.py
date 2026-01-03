import json
from pathlib import Path

import pytest

RUNTIME_EVENTS = Path("runtime_data/events.jsonl")

ALLOWED_KINDS = {"runtime", "agent", "human", "institution", "system"}


def _load_events():
    if not RUNTIME_EVENTS.exists():
        return []
    return [
        json.loads(line)
        for line in RUNTIME_EVENTS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _latest_run_events(events):
    """
    Only check the latest run (identified by the last runtime/system boot).
    This avoids legacy pollution.
    """
    boot_indices = [
        i for i, e in enumerate(events)
        if e.get("event_type") in ("system.boot", "runtime.boot")
    ]
    if not boot_indices:
        return []

    start = boot_indices[-1]
    return events[start:]


@pytest.mark.institution
def test_p01_actor_invariants():
    events = _load_events()
    assert events, "No events found in runtime_data/events.jsonl"

    run_events = _latest_run_events(events)
    assert run_events, "No events found for latest run"

    for evt in run_events:
        assert evt.get("schema_version") == "1.1", (
            "All new events must use schema_version 1.1"
        )

        assert "actor" in evt, "Event missing top-level actor"
        actor = evt["actor"]

        assert isinstance(actor, dict), "actor must be an object"

        kind = actor.get("kind")
        actor_id = actor.get("id")

        assert kind in ALLOWED_KINDS, f"Invalid actor.kind: {kind}"
        assert actor_id, "actor.id must be non-empty"
        assert actor_id != "unknown", "actor.id must not be 'unknown'"
