from __future__ import annotations

import json
from pathlib import Path

import pytest
import jsonschema
from jsonschema import Draft202012Validator


SCHEMA_PATH = Path("protocols/events/system_process_v1.schema.json")


def _load_schema() -> dict:
    assert SCHEMA_PATH.exists(), f"missing schema file: {SCHEMA_PATH}"
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_is_valid_draft202012():
    schema = _load_schema()
    Draft202012Validator.check_schema(schema)


def test_minimal_boot_and_shutdown_validate():
    schema = _load_schema()
    validator = Draft202012Validator(schema)

    minimal_boot = {
        "schema_version": "1.0",
        "event_type": "system.boot",
        "session_id": "system",
        "trace_id": "run_abc",
        "ts": "2026-01-02T20:42:34.914Z",
        "payload": {
            "system_id": "sys_x",
            "process_id": "proc_x",
            "run_id": "run_abc",
            "boot_mode": "cold",
            "started_at": "2026-01-02T20:42:34.914Z",
        },
        "payload_hash": "0" * 64,
    }
    minimal_shutdown = {
        "schema_version": "1.0",
        "event_type": "system.shutdown",
        "session_id": "system",
        "trace_id": "run_abc",
        "ts": "2026-01-02T21:00:00.000Z",
        "payload": {
            "system_id": "sys_x",
            "process_id": "proc_x",
            "run_id": "run_abc",
            "exit_reason": "normal",
        },
        "payload_hash": "f" * 64,
    }

    validator.validate(minimal_boot)
    validator.validate(minimal_shutdown)
