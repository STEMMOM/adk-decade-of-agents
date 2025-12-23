# This script is governed by P09 Observability v1.
# It performs one-way normalization from ledger-style events to canonical P09 events.
# Output is disposable and replayable; runtime MUST NEVER import this file.

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


def _iso_to_dt(ts: str) -> Optional[datetime]:
    try:
        # Accept RFC3339-ish with Z; fallback to fromisoformat with Z stripped
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _map_run_events(ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    etype = ev.get("event_type")
    if etype == "session.start":
        return {
            "event_type": "run_started",
            "run_id": ev.get("session_id"),
            "timestamp": ev.get("ts") or ev.get("timestamp"),
        }
    if etype == "session.end":
        return {
            "event_type": "run_finished",
            "run_id": ev.get("session_id"),
            "timestamp": ev.get("ts") or ev.get("timestamp"),
            "status": "success",
        }
    return None


def _map_tool_events(ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    etype = ev.get("event_type")
    payload = ev.get("payload", {}) or {}
    ts = ev.get("ts") or ev.get("timestamp")
    if etype == "tool.call":
        return {
            "event_type": "tool_call_started",
            "run_id": ev.get("session_id"),
            "timestamp": ts,
            "layer": "tool",
            "tool_name": payload.get("tool_name"),
        }
    if etype == "tool.result":
        return {
            "event_type": "tool_call_finished",
            "run_id": ev.get("session_id"),
            "timestamp": ts,
            "layer": "tool",
            "tool_name": payload.get("tool_name"),
            "status": "success",
        }
    return None


def _compute_tool_latency(mapped: Dict[str, Any], starts: Dict[Tuple[str, str], Dict[str, Any]]) -> Dict[str, Any]:
    if mapped["event_type"] != "tool_call_finished":
        return mapped
    run_id = mapped.get("run_id")
    tool_name = mapped.get("tool_name")
    key = (run_id, tool_name)
    start_ev = starts.get(key)
    if start_ev:
        t_finish = _iso_to_dt(mapped.get("timestamp", ""))
        t_start = _iso_to_dt(start_ev.get("timestamp", ""))
        if t_start and t_finish:
            delta = (t_finish - t_start).total_seconds() * 1000.0
            if delta >= 0:
                mapped = dict(mapped)
                mapped["latency_ms"] = int(delta)
    return mapped


def export(in_path: Path, out_path: Path) -> None:
    if not in_path.exists():
        raise FileNotFoundError(f"input not found: {in_path}")

    mapped_events = []
    tool_starts: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for ev in _read_jsonl(in_path):
        m = _map_run_events(ev)
        if m:
            mapped_events.append(m)
            continue

        m = _map_tool_events(ev)
        if m:
            if m["event_type"] == "tool_call_started":
                tool_starts[(m.get("run_id"), m.get("tool_name"))] = m
            elif m["event_type"] == "tool_call_finished":
                m = _compute_tool_latency(m, tool_starts)
            mapped_events.append(m)
            continue

        # Ignore unmapped events
        continue

    _write_jsonl(out_path, mapped_events)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export P09 canonical observability events (one-way normalization).")
    parser.add_argument("--in", dest="inp", required=True, help="Input ledger-style observability JSONL")
    parser.add_argument("--out", dest="out", required=True, help="Output P09 canonical observability JSONL")
    args = parser.parse_args()

    export(Path(args.inp), Path(args.out))


if __name__ == "__main__":
    main()
