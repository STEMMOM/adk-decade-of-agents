import pytest
from adk_runtime.events import append_event

def test_runtime_actor_auto_injection(monkeypatch):
    emitted = []

    # 截获最终写入的 event
    monkeypatch.setattr(
        "adk_runtime.events._write_event",
        lambda e: emitted.append(e)
    )

    append_event(
        event_type="test.event",
        payload={"x": 1}
    )

    assert emitted, "No event emitted"
    evt = emitted[0]

    assert evt["schema_version"] == "1.1"
    assert "actor" in evt
    assert evt["actor"]["kind"] == "runtime"
    assert evt["actor"]["id"]
