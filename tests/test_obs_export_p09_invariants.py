# tests/test_obs_export_p09_invariants.py
"""
P09 Observability Exporter — Invariant Tests

These tests lock the canonical semantics of obs_export_p09 output:

Invariants:
1) In exported P09 observability, run_id must ALWAYS represent system run_id
   - must be a string
   - must start with "run_"
   - must never be "unknown" or session-like (p00-...)
2) tool_call_* events must not lose session context
   - session_id must exist and be a non-empty string
3) Exporter output must be non-empty and parseable
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List


P09_OBS = Path("runtime_data/observability/observability_events_p09.jsonl")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    assert path.exists(), f"missing file: {path}"
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def test_p09_export_not_empty():
    rows = _read_jsonl(P09_OBS)
    assert rows, "P09 observability export is empty"


def test_p09_export_run_id_is_system_run_only():
    """
    All exported records must have run_id that:
    - is a string
    - starts with 'run_'
    - is never 'unknown'
    - is never a session-like id (e.g. 'p00-...')
    """
    rows = _read_jsonl(P09_OBS)

    bad = []
    for r in rows:
        run_id = r.get("run_id")

        ok = (
            isinstance(run_id, str)
            and run_id.startswith("run_")
            and run_id != "unknown"
        )

        if not ok:
            bad.append(r)
            if len(bad) >= 5:
                break

    assert not bad, f"invalid run_id found in P09 export (up to 5 samples): {bad}"


def test_p09_tool_events_require_session_id():
    """
    tool_call_started / tool_call_finished events must retain session context.
    session_id must be a non-empty string.
    """
    rows = _read_jsonl(P09_OBS)

    bad = []
    checked = 0
    for r in rows:
        et = r.get("event_type")
        if et not in ("tool_call_started", "tool_call_finished"):
            continue

        checked += 1
        session_id = r.get("session_id")

        if not (isinstance(session_id, str) and session_id.strip()):
            bad.append(r)
            if len(bad) >= 5:
                break

    # If there are no tool events at all, we don't fail the test.
    # This allows early-stage or minimal runs.
    if checked == 0:
        return

    assert not bad, f"tool events missing session_id in P09 export (up to 5 samples): {bad}"


def test_p09_export_has_only_expected_event_types():
    """
    Sanity check: P09 export should only contain known, canonical event types.
    This prevents legacy/raw observability records from leaking in.
    """
    rows = _read_jsonl(P09_OBS)

    allowed = {
        "run_started",
        "run_finished",
        "tool_call_started",
        "tool_call_finished",
    }

    bad = []
    for r in rows:
        et = r.get("event_type")
        if et not in allowed:
            bad.append(et)
            if len(bad) >= 5:
                break

    assert not bad, f"unexpected event_type(s) in P09 export: {bad}"
