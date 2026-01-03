from adk_runtime.events import append_event

def test_runtime_actor_override(monkeypatch):
    emitted = []

    monkeypatch.setattr(
        "adk_runtime.events._write_event",
        lambda e: emitted.append(e)
    )

    custom_actor = {
        "kind": "agent",
        "id": "agent:test"
    }

    append_event(
        event_type="agent.action",
        payload={},
        actor=custom_actor
    )

    evt = emitted[0]
    assert evt["actor"]["kind"] == "agent"
    assert evt["actor"]["id"] == "agent:test"
