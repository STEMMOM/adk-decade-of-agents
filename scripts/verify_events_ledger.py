from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

TS_RFC3339_MS_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

FORBIDDEN_PAYLOAD_KEYS = {"trace_id", "span_id", "parent_span_id"}

def canon_payload(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def is_v1(ev: dict) -> bool:
    return (
        ev.get("schema_version") == "1.0"
        and "payload_hash" in ev
        and "trace_id" in ev
        and isinstance(ev.get("ts"), str)
    )

def load_jsonl(path: Path) -> list[dict]:
    events = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        ev["_lineno"] = i
        events.append(ev)
    return events

def fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="runtime_data/events.jsonl", help="Path to events.jsonl")
    ap.add_argument("--fail-on-nonv1", action="store_true", help="Fail if any non-v1 events exist")
    args = ap.parse_args()

    p = Path(args.inp)
    if not p.exists():
        return fail(f"events file not found: {p}")

    events = load_jsonl(p)
    v1 = [e for e in events if is_v1(e)]
    nonv1 = [e for e in events if not is_v1(e)]

    print(f"Total events: {len(events)}")
    print(f"Event Envelope v1: {len(v1)}")
    print(f"Non-v1 (legacy/other): {len(nonv1)}")

    # Strict validation for v1 events
    for ev in v1:
        i = ev["_lineno"]
        for k in ["schema_version", "event_type", "session_id", "trace_id", "ts", "payload", "payload_hash"]:
            if k not in ev:
                return fail(f"Line {i}: missing required field {k}")

        if ev["schema_version"] != "1.0":
            return fail(f"Line {i}: schema_version != 1.0")

        if not TS_RFC3339_MS_Z.match(ev["ts"]):
            return fail(f"Line {i}: ts not RFC3339 ms Z: {ev['ts']}")

        if not isinstance(ev["payload"], dict):
            return fail(f"Line {i}: payload must be object")

        expected = sha256_hex(canon_payload(ev["payload"]))
        if ev["payload_hash"] != expected:
            return fail(
                f"Line {i}: payload_hash mismatch\n"
                f"expected={expected}\nactual={ev['payload_hash']}\n"
                f"canonical_payload={canon_payload(ev['payload'])}"
            )

        # Payload forbidden duplicate meta keys
        bad = FORBIDDEN_PAYLOAD_KEYS.intersection(ev["payload"].keys())
        if bad:
            return fail(f"Line {i}: payload contains forbidden duplicate meta keys: {sorted(bad)}")

        # Reserved payload meta fields invariants (if present)
        meta = ev["payload"]
        for k in ["_actor", "_source", "_span_id", "_parent_span_id"]:
            if k in meta and not (isinstance(meta[k], str) and meta[k]):
                return fail(f"Line {i}: payload.{k} must be non-empty string")
        if "_parent_span_id" in meta and "_span_id" not in meta:
            return fail(f"Line {i}: _parent_span_id present => _span_id must be present")
        if "tool_calls" in meta and not isinstance(meta["tool_calls"], list):
            return fail(f"Line {i}: tool_calls must be list when present")

    print("✅ All v1 events passed strict validation")

    if nonv1:
        print("\n--- Non-v1 events (report) ---")
        for ev in nonv1:
            i = ev["_lineno"]
            et = ev.get("event_type")
            ts = ev.get("ts")
            sid = ev.get("session_id")
            print(f"Line {i}: event_type={et} ts={ts!r} session_id={sid!r} keys={sorted(list(ev.keys()))}")
        if args.fail_on_nonv1:
            return fail("Non-v1 events found and --fail-on-nonv1 is set.")

    # Session sanity (optional)
    sess_types = {"session.start", "user.message", "agent.reply", "session.end"}
    sess_events = [e for e in v1 if e.get("event_type") in sess_types]
    by_session = defaultdict(list)
    for e in sess_events:
        by_session[e["session_id"]].append(e)

    for sid, seq in by_session.items():
        types = [e["event_type"] for e in seq]
        if types.count("session.start") != 1:
            return fail(f"Session {sid}: must have exactly one session.start, got {types.count('session.start')}")
        if types.count("session.end") > 1:
            return fail(f"Session {sid}: must have at most one session.end, got {types.count('session.end')}")
        if types and types[0] != "session.start":
            return fail(f"Session {sid}: first must be session.start, got {types[0]}")
        if "session.end" in types:
            end_idx = types.index("session.end")
            if any(t in ("user.message", "agent.reply") for t in types[end_idx + 1 :]):
                return fail(f"Session {sid}: messages after session.end")

    print("✅ Session semantics sanity checks passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
