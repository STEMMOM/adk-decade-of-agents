#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set


@dataclass
class Node:
    span_id: str
    parent_span_id: Optional[str]
    event_type: str
    actor: str
    ts: str
    session_id: str
    trace_id: str
    payload: Dict[str, Any]


def _shorten(s: str, n: int = 80) -> str:
    s = s.replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
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


def _extract_node(row: Dict[str, Any]) -> Optional[Node]:
    """
    Expects P04 envelope with P05 fields stored in payload:
      payload._span_id
      payload._parent_span_id
      payload._actor
    Returns None for rows that don't have a span_id.
    """
    payload = row.get("payload") or {}
    span_id = payload.get("_span_id")
    if not span_id:
        return None

    return Node(
        span_id=str(span_id),
        parent_span_id=(str(payload.get("_parent_span_id")) if payload.get("_parent_span_id") else None),
        event_type=str(row.get("event_type", "")),
        actor=str(payload.get("_actor", "unknown")),
        ts=str(row.get("ts", "")),
        session_id=str(row.get("session_id", "")),
        trace_id=str(row.get("trace_id", "")),
        payload=payload,
    )


def _group_key(n: Node) -> Tuple[str, str]:
    return (n.session_id, n.trace_id)


def _build_tree(nodes: List[Node]) -> Tuple[Dict[str, Node], Dict[str, List[str]], List[str], List[str]]:
    """
    Returns:
      - id2node
      - children_map: parent_span_id -> [child_span_id...]
      - roots: span_ids whose parent is None or missing
      - orphans: span_ids whose parent_span_id references a missing node
    """
    id2node: Dict[str, Node] = {n.span_id: n for n in nodes}

    children: Dict[str, List[str]] = {}
    orphans: List[str] = []
    roots: List[str] = []

    for n in nodes:
        pid = n.parent_span_id
        if pid is None:
            roots.append(n.span_id)
            continue
        if pid not in id2node:
            orphans.append(n.span_id)
            roots.append(n.span_id)  # treat orphan as root for display
            continue
        children.setdefault(pid, []).append(n.span_id)

    # stable ordering: by timestamp then event_type
    for pid, kids in children.items():
        kids.sort(key=lambda sid: (id2node[sid].ts, id2node[sid].event_type))

    roots.sort(key=lambda sid: (id2node[sid].ts, id2node[sid].event_type))
    return id2node, children, roots, orphans


def _fmt_node(n: Node, show_payload: bool = True) -> str:
    # pick a human-friendly summary from payload
    summary = ""
    if n.event_type == "user.message":
        summary = _shorten(str(n.payload.get("text", "")))
    elif n.event_type == "agent.reply":
        summary = _shorten(str(n.payload.get("reply", "")))
    elif "message" in n.payload:
        summary = _shorten(str(n.payload.get("message", "")))

    base = f"{n.event_type}  actor={n.actor}  span={n.span_id}"
    if n.parent_span_id:
        base += f"  parent={n.parent_span_id}"
    if n.ts:
        base += f"  ts={n.ts}"
    if summary:
        base += f"\n    ↳ {summary}"

    if show_payload:
        # show a trimmed payload without noisy keys
        p = dict(n.payload)
        p.pop("_source", None)
        p.pop("_actor", None)
        p.pop("_span_id", None)
        p.pop("_parent_span_id", None)
        if p:
            base += f"\n    payload={_shorten(json.dumps(p, ensure_ascii=False), 140)}"
    return base


def _detect_cycle(id2node: Dict[str, Node], children: Dict[str, List[str]], roots: List[str]) -> bool:
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

    for r in roots:
        if dfs(r):
            return True
    return False


def _print_tree(id2node: Dict[str, Node], children: Dict[str, List[str]], root: str, indent: str = "", last: bool = True,
                show_payload: bool = True, max_depth: Optional[int] = None, _depth: int = 0) -> None:
    prefix = "└─ " if last else "├─ "
    if indent == "":
        # root line
        print(_fmt_node(id2node[root], show_payload=show_payload))
    else:
        print(indent + prefix + _fmt_node(id2node[root], show_payload=show_payload).replace("\n", "\n" + indent + ("   " if last else "│  ")))

    if max_depth is not None and _depth >= max_depth:
        if children.get(root):
            print(indent + ("   " if last else "│  ") + "└─ … (max depth reached)")
        return

    kids = children.get(root, [])
    for i, c in enumerate(kids):
        is_last = i == len(kids) - 1
        next_indent = indent + ("   " if last else "│  ")
        _print_tree(id2node, children, c, indent=next_indent, last=is_last, show_payload=show_payload, max_depth=max_depth, _depth=_depth + 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render causal trace tree from runtime_data/events.jsonl")
    ap.add_argument("--file", default="runtime_data/events.jsonl", help="Path to events.jsonl")
    ap.add_argument("--session", default=None, help="Filter by session_id (exact match)")
    ap.add_argument("--trace", default=None, help="Filter by trace_id (exact match)")
    ap.add_argument("--no-payload", action="store_true", help="Hide payload details")
    ap.add_argument("--max-depth", type=int, default=None, help="Max depth to render")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"[ERROR] File not found: {path}")

    rows = _read_jsonl(path)
    nodes_all: List[Node] = []
    for r in rows:
        n = _extract_node(r)
        if n:
            nodes_all.append(n)

    if not nodes_all:
        raise SystemExit("[ERROR] No span-based events found. (Missing payload._span_id?)")

    # group by (session_id, trace_id)
    groups: Dict[Tuple[str, str], List[Node]] = {}
    for n in nodes_all:
        if args.session and n.session_id != args.session:
            continue
        if args.trace and n.trace_id != args.trace:
            continue
        groups.setdefault(_group_key(n), []).append(n)

    if not groups:
        raise SystemExit("[ERROR] No events match the given filters.")

    for (session_id, trace_id), nodes in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        nodes.sort(key=lambda x: (x.ts, x.event_type))
        id2node, children, roots, orphans = _build_tree(nodes)

        print("\n" + "=" * 88)
        print(f"SESSION: {session_id}")
        print(f"TRACE:   {trace_id}")
        print(f"EVENTS:  {len(nodes)}  | ROOTS: {len(roots)}  | ORPHANS: {len(orphans)}")
        if orphans:
            print("WARN: orphan spans (parent missing):")
            for sid in orphans:
                print(f"  - {sid} (parent={id2node[sid].parent_span_id})")

        if _detect_cycle(id2node, children, roots):
            print("ERROR: cycle detected in span graph (this should never happen).")
            # still print what we can

        for i, r in enumerate(roots):
            print("\n--- ROOT", i + 1, "---")
            _print_tree(
                id2node,
                children,
                r,
                indent="",
                last=True,
                show_payload=not args.no_payload,
                max_depth=args.max_depth,
            )

    print("\nDone.")


if __name__ == "__main__":
    main()
