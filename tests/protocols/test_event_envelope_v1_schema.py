import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "protocols/events/event_envelope_v1.schema.json"
EXAMPLE_JSONL = REPO_ROOT / "examples/events/event_envelope_v1.example.jsonl"


def _load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        raise AssertionError(f"Missing schema file: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        yield i, json.loads(line)


def test_schema_is_valid_draft_2020_12():
    schema = _load_schema()
    Draft202012Validator.check_schema(schema)


def test_example_jsonl_conforms_to_schema_if_present():
    """
    If the example file exists, it must validate.
    (This test allows you to keep the example file optional early on,
     but once present it becomes enforceable.)
    """
    if not EXAMPLE_JSONL.exists():
        pytest.skip(f"No example jsonl found at {EXAMPLE_JSONL}")

    schema = _load_schema()
    validator = Draft202012Validator(schema)

    for lineno, obj in _iter_jsonl(EXAMPLE_JSONL):
        errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
        if errors:
            msg = "\n".join(
                [f"Line {lineno}: schema validation failed"] +
                [f"- {list(err.path)}: {err.message}" for err in errors]
            )
            raise AssertionError(msg)
