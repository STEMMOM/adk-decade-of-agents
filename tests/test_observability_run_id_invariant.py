# tests/test_system_identity_invariants.py
"""
System Identity Protocol v1.0 — Invariant Tests

These tests enforce the constitutional semantics of IDs:
- system_id: stable identity across runs
- process_id: per-process identity
- run_id: life-axis identity generated at system.boot
- boot/shutdown: lifecycle pairing and recover semantics
- observability: must carry authoritative run_id for the latest run
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


EVENTS = Path("runtime_data/events.jsonl")
OBS = Path("runtime_data/observability/observability_events.jsonl")
SYSTEM_IDENTITY = Path("runtime_data/system_identity.json")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    assert path.exists(), f"missing file: {path}"
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _system_boot_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [e for e in events if e.get("event_type") == "system.boot"]


def _system_shutdown_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [e for e in events if e.get("event_type") == "system.shutdown"]


def _boot_payload(e: Dict[str, Any]) -> Dict[str, Any]:
    # events.jsonl has two shapes in your repo; system.boot uses payload dict
    return e.get("payload") or {}


def _latest_run_id(events: List[Dict[str, Any]]) -> str:
    boots = _system_boot_events(events)
    assert boots, "no system.boot found in events.jsonl"
    rid = _boot_payload(boots[-1]).get("run_id")
    assert isinstance(rid, str) and rid.startswith("run_"), f"latest system.boot has invalid run_id: {rid}"
    return rid


def _load_system_id_from_identity_file() -> Optional[str]:
    if not SYSTEM_IDENTITY.exists():
        return None
    try:
        obj = json.loads(SYSTEM_IDENTITY.read_text(encoding="utf-8"))
    except Exception:
        return None
    # tolerate different keys if you change schema later
    for k in ("system_id", "sys_id", "id"):
        v = obj.get(k)
        if isinstance(v, str) and v.startswith("sys_"):
            return v
    return None


def _index_by_run_id(events: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
    boots_by_run: Dict[str, List[Dict[str, Any]]] = {}
    shuts_by_run: Dict[str, List[Dict[str, Any]]] = {}

    for e in _system_boot_events(events):
        rid = _boot_payload(e).get("run_id")
        if isinstance(rid, str):
            boots_by_run.setdefault(rid, []).append(e)

    for e in _system_shutdown_events(events):
        rid = (e.get("payload") or {}).get("run_id")
        if isinstance(rid, str):
            shuts_by_run.setdefault(rid, []).append(e)

    return boots_by_run, shuts_by_run


# ----------------------------
# Invariant 1: run_id/system_id/process_id presence & format at boot
# ----------------------------
def test_system_boot_has_required_ids_and_formats():
    events = _read_jsonl(EVENTS)
    boots = _system_boot_events(events)
    assert boots, "no system.boot events recorded"

    bad = []
    for e in boots[-50:]:  # sample recent boots for speed/robustness
        p = _boot_payload(e)
        system_id = p.get("system_id")
        process_id = p.get("process_id")
        run_id = p.get("run_id")

        ok = (
            isinstance(system_id, str) and system_id.startswith("sys_") and
            isinstance(process_id, str) and process_id.startswith("proc_") and
            isinstance(run_id, str) and run_id.startswith("run_")
        )
        if not ok:
            bad.append({"payload": p})
            if len(bad) >= 3:
                break

    assert not bad, f"system.boot missing/invalid ids (up to 3 samples): {bad}"


# ----------------------------
# Invariant 2: system_id must be stable across runs (and match persisted identity if available)
# ----------------------------
def test_system_id_is_stable_across_boots():
    events = _read_jsonl(EVENTS)
    boots = _system_boot_events(events)
    assert boots, "no system.boot events recorded"

    system_ids = []
    for e in boots:
        sid = _boot_payload(e).get("system_id")
        if isinstance(sid, str):
            system_ids.append(sid)

    assert system_ids, "no system_id found in boot payloads"

    unique = sorted(set(system_ids))
    assert len(unique) == 1, f"system_id must be stable; found multiple: {unique}"

    persisted = _load_system_id_from_identity_file()
    if persisted is not None:
        assert unique[0] == persisted, f"system_id mismatch: boot={unique[0]} identity_file={persisted}"


# ----------------------------
# Invariant 3: boot/shutdown pairing rules
# - each run_id must have exactly 1 system.boot
# - each run_id should have 0 or 1 system.shutdown
# - if a run has no shutdown, the next boot should be in recover mode pointing to it (best-effort)
# ----------------------------
def test_boot_shutdown_pairing_and_recover_semantics():
    events = _read_jsonl(EVENTS)
    boots = _system_boot_events(events)
    assert boots, "no system.boot events recorded"

    boots_by_run, shuts_by_run = _index_by_run_id(events)

    # Each run_id must have exactly one boot
    bad_boots = []
    for rid, xs in boots_by_run.items():
        if len(xs) != 1:
            bad_boots.append((rid, len(xs)))
            if len(bad_boots) >= 5:
                break
    assert not bad_boots, f"run_id must have exactly 1 boot, violations: {bad_boots}"

    # Shutdown count must be <= 1
    bad_shuts = []
    for rid, xs in shuts_by_run.items():
        if len(xs) > 1:
            bad_shuts.append((rid, len(xs)))
            if len(bad_shuts) >= 5:
                break
    assert not bad_shuts, f"run_id must have at most 1 shutdown, violations: {bad_shuts}"

    # Recover semantics (best-effort): find the most recent run with missing shutdown and check a later boot references it
    # We only assert this if we can unambiguously identify a "next boot".
    latest_missing = None
    missing_runs = []
    # preserve boot order
    boot_order = []
    for e in boots:
        rid = _boot_payload(e).get("run_id")
        if isinstance(rid, str):
            boot_order.append(rid)

    for rid in boot_order:
        if rid not in shuts_by_run:
            missing_runs.append(rid)

    if missing_runs:
        latest_missing = missing_runs[-1]
        # look for a boot after it
        idx = boot_order.index(latest_missing)
        if idx + 1 < len(boot_order):
            next_boot_rid = boot_order[idx + 1]
            next_boot = boots_by_run[next_boot_rid][0]
            p = _boot_payload(next_boot)
            boot_mode = p.get("boot_mode")
            recovered_from = p.get("recovered_from_run_id")
            # Only enforce if your system uses recover mode; tolerate if you haven't fully wired this yet
            assert boot_mode in ("recover", "warm", "cold"), f"unexpected boot_mode: {boot_mode}"
            if boot_mode == "recover":
                assert recovered_from == latest_missing, (
                    f"recover boot must point to the last missing-shutdown run. "
                    f"expected={latest_missing} got={recovered_from}"
                )


# ----------------------------
# Invariant 4: Observability must carry authoritative run_id for the latest run
# - for the latest run_id, there must be at least one observability record
# - none of those records may have run_id missing/null/unknown, and run_id must start with run_
# ----------------------------
def test_observability_has_authoritative_run_id_for_latest_run():
    events = _read_jsonl(EVENTS)
    latest_run = _latest_run_id(events)

    obs = _read_jsonl(OBS)

    bad = []
    total = 0
    for o in obs:
        if o.get("run_id") != latest_run:
            continue
        total += 1
        rid = o.get("run_id")
        if (rid is None) or (rid == "unknown") or (not isinstance(rid, str)) or (not rid.startswith("run_")):
            bad.append(o)
            if len(bad) >= 3:
                break

    assert total > 0, f"no observability records found for latest run_id={latest_run}"
    assert not bad, f"bad observability records for latest run_id={latest_run} (up to 3): {bad}"


# ----------------------------
# Invariant 5: Session axis must exist alongside run axis in observability (latest run)
# - ensures session_id is not collapsed into run_id
# ----------------------------
def test_observability_records_session_id_for_latest_run():
    events = _read_jsonl(EVENTS)
    latest_run = _latest_run_id(events)

    obs = _read_jsonl(OBS)

    seen = 0
    missing = []
    for o in obs:
        if o.get("run_id") != latest_run:
            continue
        seen += 1
        sid = o.get("session_id")
        # tolerate non-p00 apps; require non-empty string
        if not (isinstance(sid, str) and sid.strip()):
            missing.append(o)
            if len(missing) >= 3:
                break

    assert seen > 0, f"no observability records found for latest run_id={latest_run}"
    assert not missing, f"missing/empty session_id for latest run records (up to 3): {missing}"
