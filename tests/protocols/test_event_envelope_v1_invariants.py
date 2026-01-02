import hashlib
import json
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_JSONL = REPO_ROOT / "examples/events/event_envelope_v1.example.jsonl"


TS_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
HEX64_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def canonicalize_payload(payload: dict) -> str:
    """
    Canonicalization contract (must match protocol):
    - keys sorted
    - no whitespace (compact separators)
    - ensure_ascii=False (do not escape non-ASCII)
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def compute_payload_hash(payload: dict) -> str:
    return sha256_hex(canonicalize_payload(payload))


def _iter_jsonl(path: Path):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        yield i, json.loads(line)


@pytest.mark.parametrize(
    "obj",
    [
        {
            "schema_version": "1.0",
            "event_type": "user.message",
            "session_id": "p00-demo-session",
            "trace_id": "9b9b9c1e-2b1c-4df6-9e42-7a1b5e2b6d3a",
            "ts": "2024-12-17T03:21:45.123Z",
            "payload": {"text": "Hello, world."},
            # computed below in test
            "payload_hash": "",
        }
    ],
)
def test_invariant_payload_hash_matches_canonical_payload(obj):
    obj["payload_hash"] = compute_payload_hash(obj["payload"])
    assert HEX64_PATTERN.match(obj["payload_hash"]), "payload_hash must be 64 hex chars"
    assert obj["payload_hash"] == compute_payload_hash(obj["payload"])


def test_invariant_required_fields_and_types_minimal():
    obj = {
        "schema_version": "1.0",
        "event_type": "session.start",
        "session_id": "sess_1",
        "trace_id": "trace_1",
        "ts": "2024-12-17T03:21:45.123Z",
        "payload": {},
        "payload_hash": compute_payload_hash({}),
    }

    # Required presence
    for k in ["schema_version", "event_type", "session_id", "trace_id", "ts", "payload", "payload_hash"]:
        assert k in obj, f"missing required field: {k}"

    # Types
    assert isinstance(obj["schema_version"], str)
    assert isinstance(obj["event_type"], str) and obj["event_type"]
    assert isinstance(obj["session_id"], str) and obj["session_id"]
    assert isinstance(obj["trace_id"], str) and obj["trace_id"]
    assert isinstance(obj["ts"], str)
    assert isinstance(obj["payload"], dict)
    assert isinstance(obj["payload_hash"], str)

    # Fixed schema_version for v1
    assert obj["schema_version"] == "1.0"

    # Timestamp format
    assert TS_PATTERN.match(obj["ts"]), f"ts must match pattern: {obj['ts']}"

    # Hash format + correctness
    assert HEX64_PATTERN.match(obj["payload_hash"])
    assert obj["payload_hash"] == compute_payload_hash(obj["payload"])


def test_example_jsonl_payload_hash_correctness_if_present():
    """
    If example exists, enforce payload_hash correctness too.
    NOTE: Your current example uses an all-zero placeholder; this test will fail
    until you replace it with the correct computed hash.
    """
    if not EXAMPLE_JSONL.exists():
        pytest.skip(f"No example jsonl found at {EXAMPLE_JSONL}")

    for lineno, obj in _iter_jsonl(EXAMPLE_JSONL):
        # Required fields check (lightweight)
        for k in ["schema_version", "event_type", "session_id", "trace_id", "ts", "payload", "payload_hash"]:
            assert k in obj, f"Line {lineno}: missing required field: {k}"

        assert obj["schema_version"] == "1.0", f"Line {lineno}: schema_version must be '1.0'"
        assert isinstance(obj["payload"], dict), f"Line {lineno}: payload must be object"
        assert isinstance(obj["payload_hash"], str), f"Line {lineno}: payload_hash must be string"

        assert TS_PATTERN.match(obj["ts"]), f"Line {lineno}: invalid ts format: {obj['ts']}"
        assert HEX64_PATTERN.match(obj["payload_hash"]), f"Line {lineno}: payload_hash must be 64 hex chars"

        expected = compute_payload_hash(obj["payload"])
        assert obj["payload_hash"] == expected, (
            f"Line {lineno}: payload_hash mismatch\n"
            f"expected: {expected}\n"
            f"actual:   {obj['payload_hash']}\n"
            f"canonical_payload: {canonicalize_payload(obj['payload'])}"
        )
def canonicalize_envelope_projection(event: dict) -> str:
    """
    Envelope hash canonicalization contract (v1):
    Projection include-set:
      required: schema_version, event_type, session_id, trace_id, ts, payload_hash
      optional: prev_envelope_hash (only if present)
    Excludes:
      - envelope_hash (self)
      - payload (already committed by payload_hash)
      - any other extension fields
    Serialization:
      - sort_keys=True
      - separators=(",", ":")
      - ensure_ascii=False
    """
    required_keys = ["schema_version", "event_type", "session_id", "trace_id", "ts", "payload_hash"]
    projection = {k: event[k] for k in required_keys}

    if "prev_envelope_hash" in event:
        projection["prev_envelope_hash"] = event["prev_envelope_hash"]

    return json.dumps(
        projection,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_envelope_hash(event: dict) -> str:
    return sha256_hex(canonicalize_envelope_projection(event))


def test_invariant_envelope_hash_matches_projection_when_present():
    obj = {
        "schema_version": "1.0",
        "event_type": "user.message",
        "session_id": "sess_1",
        "trace_id": "trace_1",
        "ts": "2024-12-17T03:21:45.123Z",
        "payload": {"text": "Hello"},
        "payload_hash": compute_payload_hash({"text": "Hello"}),
    }

    # Case 1: envelope_hash absent is allowed
    assert "envelope_hash" not in obj

    # Case 2: when present, must match computed projection hash
    obj["envelope_hash"] = compute_envelope_hash(obj)
    assert HEX64_PATTERN.match(obj["envelope_hash"])
    assert obj["envelope_hash"] == compute_envelope_hash(obj)

    # Case 3: prev_envelope_hash inclusion changes envelope_hash deterministically
    obj2 = dict(obj)
    obj2["prev_envelope_hash"] = "a" * 64
    obj2["envelope_hash"] = compute_envelope_hash(obj2)
    assert obj2["envelope_hash"] != obj["envelope_hash"]
    assert obj2["envelope_hash"] == compute_envelope_hash(obj2)

    # Case 4: extra extension fields MUST NOT affect envelope_hash (excluded from projection)
    obj3 = dict(obj2)
    obj3["some_future_field"] = {"x": 1}
    # envelope_hash MUST remain same because projection excludes unknown fields
    assert compute_envelope_hash(obj3) == compute_envelope_hash(obj2)


def test_example_jsonl_envelope_hash_correctness_if_present():
    """
    If an example line includes envelope_hash, enforce correctness.
    (We do not require examples to include envelope_hash.)
    """
    if not EXAMPLE_JSONL.exists():
        pytest.skip(f"No example jsonl found at {EXAMPLE_JSONL}")

    for lineno, obj in _iter_jsonl(EXAMPLE_JSONL):
        if "envelope_hash" not in obj:
            continue

        assert isinstance(obj["envelope_hash"], str), f"Line {lineno}: envelope_hash must be string"
        assert HEX64_PATTERN.match(obj["envelope_hash"]), f"Line {lineno}: envelope_hash must be 64 hex chars"

        expected = compute_envelope_hash(obj)
        assert obj["envelope_hash"] == expected, (
            f"Line {lineno}: envelope_hash mismatch\n"
            f"expected: {expected}\n"
            f"actual:   {obj['envelope_hash']}\n"
            f"canonical_envelope_projection: {canonicalize_envelope_projection(obj)}"
        )
