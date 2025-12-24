#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass
class Event:
    event_type: str
    ts: str
    session_id: str
    trace_id: str
    payload: Dict[str, Any]
    payload_hash: str
    span_id: Optional[str]
    parent_span_id: Optional[str]
    actor: Optional[str]


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"[ERROR] Invalid JSON on line {i}: {e}") from e
    return rows


def parse_event(row: Dict[str, Any]) -> Event:
    payload = row.get("payload") or {}
    return Event(
        event_type=str(row.get("event_type", "")),
        ts=str(row.get("ts", "")),
        session_id=str(row.get("session_id", "")),
        trace_id=str(row.get("trace_id", "")),
        payload=payload,
        payload_hash=str(row.get("payload_hash", "")),
        span_id=(str(payload.get("_span_id")) if payload.get("_span_id") else None),
        parent_span_id=(str(payload.get("_parent_span_id")) if payload.get("_parent_span_id") else None),
        actor=(str(payload.get("_actor")) if payload.get("_actor") else None),
    )


def verify_payload_hash(e: Event) -> Optional[str]:
    calc = sha256_hex(canonical_json(e.payload))
    if calc != e.payload_hash:
        return f"payload_hash mismatch: expected={e.payload_hash} calc={calc} event_type={e.event_type}"
    return None


def build_span_index(events: List[Event]) -> Tuple[Dict[str, Event], Dict[str, List[str]], List[str], List[str]]:
    span2event: Dict[str, Event] = {}
    for e in events:
        if e.span_id and e.span_id not in span2event:
            span2event[e.span_id] = e

    children: Dict[str, List[str]] = {}
    roots: List[str] = []
    orphans: List[str] = []

    for sid, ev in span2event.items():
        pid = ev.parent_span_id
        if pid is None:
            roots.append(sid)
        else:
            if pid not in span2event:
                orphans.append(sid)
                roots.append(sid)  # displayable root
            else:
                children.setdefault(pid, []).append(sid)

    def key(sid: str) -> Tuple[str, str]:
        ev = span2event[sid]
        return (ev.ts, ev.event_type)

    for pid, kids in children.items():
        kids.sort(key=key)
    roots.sort(key=key)

    return span2event, children, roots, orphans


def detect_cycle(children: Dict[str, List[str]], roots: List[str]) -> bool:
    visited: Set[str] = set()
    stack: Set[str] = set()

    def dfs(sid: str) -> bool:
        if sid in stack:
            return True
        if sid in visited:
            return False
        visited.add(sid)
        stack.add(sid)
        for c in children.get(sid, []):
            if dfs(c):
                return True
        stack.remove(sid)
        return False

    return any(dfs(r) for r in roots)


def _walk_tree(span2event: Dict[str, Event], children: Dict[str, List[str]], root: str) -> List[str]:
    lines: List[str] = []

    def walk(sid: str, depth: int = 0):
        ev = span2event[sid]
        indent = "  " * depth
        actor = ev.actor or "unknown"
        lines.append(f"{indent}- {ev.event_type} actor={actor} ts={ev.ts}")

        p = ev.payload
        if ev.event_type == "user.message":
            lines.append(f"{indent}    user: {p.get('text','')}")
        elif ev.event_type == "agent.reply":
            lines.append(f"{indent}    agent: {p.get('reply','')}")
            tc = p.get("tool_calls")
            if isinstance(tc, list):
                lines.append(f"{indent}    tool_calls_declared: {len(tc)}")
        elif ev.event_type == "tool.call":
            lines.append(f"{indent}    tool.call: {p.get('tool_name')} args={p.get('args')}")
        elif ev.event_type == "tool.result":
            lines.append(f"{indent}    tool.result: {p.get('tool_name')} result={p.get('result')}")
        elif ev.event_type == "tool.error":
            lines.append(f"{indent}    tool.error: {p.get('tool_name')} error={p.get('error')}")

        for c in children.get(sid, []):
            walk(c, depth + 1)

    walk(root, 0)
    return lines


def _count_declared_tool_calls(events: List[Event]) -> int:
    # sum over agent.reply payload.tool_calls length (if list)
    total = 0
    for e in events:
        if e.event_type == "agent.reply":
            tc = e.payload.get("tool_calls")
            if isinstance(tc, list):
                total += len(tc)
    return total


def _find_root_span(span2event: Dict[str, Event], roots: List[str]) -> Optional[str]:
    for sid in roots:
        if span2event[sid].event_type == "session.start":
            return sid
    return roots[0] if roots else None


def _children_of(children: Dict[str, List[str]], sid: str) -> List[str]:
    return children.get(sid, [])


def replay_and_validate(events: List[Event], strict: bool = False) -> Dict[str, Any]:
    warnings: List[str] = []
    errors: List[str] = []
    validations: Dict[str, Any] = {}

    # ---- hash checks (P04)
    for e in events:
        err = verify_payload_hash(e)
        if err:
            if strict:
                errors.append(err)
            else:
                warnings.append(err)

    # ---- build graph
    span2event, children, roots, orphans = build_span_index(events)

    validations["graph"] = {
        "span_count": len(span2event),
        "root_count": len(roots),
        "orphan_count": len(orphans),
        "cycle_detected": detect_cycle(children, roots),
    }
    if validations["graph"]["cycle_detected"]:
        errors.append("cycle detected in span graph")
    if orphans:
        errors.append(f"orphan spans detected: {len(orphans)}")

    root_sid = _find_root_span(span2event, roots)
    if not root_sid:
        errors.append("missing root span (session.start)")
        root_sid = roots[0] if roots else None

    # ---- required events
    has_start = any(e.event_type == "session.start" for e in events)
    has_end = any(e.event_type == "session.end" for e in events)
    validations["required_events"] = {"session.start": has_start, "session.end": has_end}
    if not has_start:
        errors.append("missing session.start")
    if not has_end:
        errors.append("missing session.end")

    # ---- session.end must parent=root (P05 v1)
    end_parent_ok = None
    end_sid = None
    for sid, ev in span2event.items():
        if ev.event_type == "session.end":
            end_sid = sid
            end_parent_ok = (ev.parent_span_id == root_sid)
            break
    validations["session_end_parent_root"] = {
        "ok": bool(end_parent_ok) if end_parent_ok is not None else False,
        "root_span_id": root_sid,
        "session_end_span_id": end_sid,
        "session_end_parent_span_id": span2event[end_sid].parent_span_id if end_sid else None,
    }
    if end_parent_ok is False:
        errors.append("session.end parent != root_span_id")

    # ---- tool.call must have tool.result or tool.error child
    tool_calls: List[str] = []
    tool_results: List[str] = []
    tool_errors: List[str] = []
    for sid, ev in span2event.items():
        if ev.event_type == "tool.call":
            tool_calls.append(sid)
            kids = _children_of(children, sid)
            ok = any(span2event[k].event_type in ("tool.result", "tool.error") for k in kids)
            if not ok:
                errors.append(f"tool.call missing tool.result/tool.error child: span_id={sid}")
        elif ev.event_type == "tool.result":
            tool_results.append(sid)
            # parent must be tool.call
            pid = ev.parent_span_id
            if pid and pid in span2event and span2event[pid].event_type != "tool.call":
                errors.append("tool.result parent must be tool.call")
        elif ev.event_type == "tool.error":
            tool_errors.append(sid)
            pid = ev.parent_span_id
            if pid and pid in span2event and span2event[pid].event_type != "tool.call":
                errors.append("tool.error parent must be tool.call")

    validations["tool_chain"] = {
        "tool_calls_observed": len(tool_calls),
        "tool_results_observed": len(tool_results),
        "tool_errors_observed": len(tool_errors),
    }

    # ---- declared tool_calls vs observed tool.call (accounting)
    declared = _count_declared_tool_calls(events)
    observed = len(tool_calls)
    validations["tool_call_accounting"] = {
        "declared_tool_calls": declared,
        "observed_tool_call_events": observed,
        "ok": declared == observed,
    }
    if declared != observed:
        errors.append(f"tool_call accounting mismatch: declared={declared} observed={observed}")

    # ---- build replay lines
    replay_lines: List[str] = []
    if root_sid:
        replay_lines = _walk_tree(span2event, children, root_sid)

    # ---- finalize
    report = {
        "session_id": events[0].session_id if events else None,
        "trace_ids": sorted({e.trace_id for e in events}),
        "event_count": len(events),
        "warnings": warnings,
        "errors": errors,
        "validations": validations,
        "replay_lines": replay_lines,
    }

    if strict and errors:
        # strict means fail hard
        raise SystemExit("[ERROR] Strict replay failed:\n- " + "\n- ".join(errors))

    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="P06 Replay Runner (hardened)")
    ap.add_argument("--file", default="runtime_data/events.jsonl", help="Path to events.jsonl")
    ap.add_argument("--session", default=None, help="Replay only a specific session_id")
    ap.add_argument("--strict", action="store_true", help="Fail on any validation error (and hash mismatch)")
    ap.add_argument("--out", default=None, help="Write replay report JSON to this path (single file)")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"[ERROR] File not found: {path}")

    rows = read_jsonl(path)
    events_all = [parse_event(r) for r in rows]

    sessions: Dict[str, List[Event]] = {}
    for e in events_all:
        if args.session and e.session_id != args.session:
            continue
        sessions.setdefault(e.session_id, []).append(e)

    if not sessions:
        raise SystemExit("[ERROR] No sessions found (check --session filter or file).")

    all_reports: List[Dict[str, Any]] = []
    for sid, evs in sorted(sessions.items(), key=lambda kv: kv[0]):
        evs.sort(key=lambda e: (e.ts, e.event_type))
        report = replay_and_validate(evs, strict=args.strict)
        all_reports.append(report)

        print("\n" + "=" * 88)
        print(f"REPLAY SESSION: {sid}")
        print(f"TRACE_IDS: {report['trace_ids']}")
        print(f"EVENTS: {report['event_count']}")
        if report["warnings"]:
            print("\nWARNINGS:")
            for w in report["warnings"]:
                print(" -", w)
        if report["errors"]:
            print("\nERRORS:")
            for e in report["errors"]:
                print(" -", e)

        print("\nREPLAY OUTPUT:")
        for line in report["replay_lines"]:
            print(line)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"reports": all_reports} if len(all_reports) > 1 else all_reports[0]
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote replay report: {out_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
