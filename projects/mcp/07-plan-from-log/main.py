#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP-07 — Plan-from-Log
Compile policy decision logs (JSONL) into a replay plan (JSON).

Invariants:
- Plan is derived ONLY from log (no guessing, no补全).
- Each step records:
  - uri
  - expect.decision  (ALLOW/DENY)
  - expect.error_code (only when DENY and available)
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ----------------------------
# Models
# ----------------------------

@dataclass(frozen=True)
class Expect:
    decision: str
    error_code: Optional[str] = None


@dataclass(frozen=True)
class Step:
    uri: str
    expect: Expect


@dataclass
class Plan:
    schema_version: str
    source: Dict[str, Any]
    roots_hash: Optional[str]
    steps: List[Dict[str, Any]]  # serialized Step dicts


# ----------------------------
# IO helpers
# ----------------------------

def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"input jsonl not found: {path}")
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at {path}:{line_no}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL row must be object at {path}:{line_no}")
            rows.append(obj)
    return rows


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ----------------------------
# Extraction
# ----------------------------

def _get_uri(row: Dict[str, Any]) -> Optional[str]:
    # Try common layouts, but do NOT invent data.
    # Accept:
    # - row["uri"]
    # - row["request"]["uri"]
    # - row["resource"]["uri"]
    if isinstance(row.get("uri"), str):
        return row["uri"]
    req = row.get("request")
    if isinstance(req, dict) and isinstance(req.get("uri"), str):
        return req["uri"]
    res = row.get("resource")
    if isinstance(res, dict) and isinstance(res.get("uri"), str):
        return res["uri"]
    return None


def _get_decision(row: Dict[str, Any]) -> Optional[str]:
    # Accept:
    # - row["decision"]
    # - row["result"]["decision"]
    d = row.get("decision")
    if isinstance(d, str):
        return d
    r = row.get("result")
    if isinstance(r, dict) and isinstance(r.get("decision"), str):
        return r["decision"]
    return None


def _get_error_code(row: Dict[str, Any]) -> Optional[str]:
    # Only meaningful for DENY. Accept:
    # - row["error_code"]
    # - row["result"]["error_code"]
    e = row.get("error_code")
    if isinstance(e, str):
        return e
    r = row.get("result")
    if isinstance(r, dict) and isinstance(r.get("error_code"), str):
        return r["error_code"]
    return None


def _get_roots_hash(row: Dict[str, Any]) -> Optional[str]:
    # Accept:
    # - row["roots_hash"]
    # - row["roots"]["hash"]
    # - row["policy"]["roots_hash"] (policy state snapshot)
    rh = row.get("roots_hash")
    if isinstance(rh, str):
        return rh
    roots = row.get("roots")
    if isinstance(roots, dict) and isinstance(roots.get("hash"), str):
        return roots["hash"]
    policy = row.get("policy")
    if isinstance(policy, dict) and isinstance(policy.get("roots_hash"), str):
        return policy["roots_hash"]
    return None


def _get_allowed_roots(row: Dict[str, Any]) -> Optional[List[str]]:
    policy = row.get("policy")
    if isinstance(policy, dict):
        ar = policy.get("allowed_roots")
        if isinstance(ar, list) and all(isinstance(x, str) for x in ar):
            return ar
    return None


def _get_ts(row: Dict[str, Any]) -> Optional[float]:
    # Optional ordering key. Accept numeric timestamps.
    # - row["timestamp"] or row["ts"]
    for k in ("timestamp", "ts"):
        v = row.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def normalize_log_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Keep only rows that can produce a valid step (uri + decision).
    Do NOT fill missing values.
    """
    out: List[Dict[str, Any]] = []
    for row in rows:
        uri = _get_uri(row)
        decision = _get_decision(row)
        if not uri or not decision:
            continue
        # normalize decision to uppercase for stability
        decision_norm = decision.strip().upper()
        if decision_norm not in ("ALLOW", "DENY"):
            continue
        allowed_roots = _get_allowed_roots(row)
        out.append({
            "_raw": row,
            "uri": uri,
            "decision": decision_norm,
            "error_code": _get_error_code(row),
            "roots_hash": _get_roots_hash(row),
            "allowed_roots": allowed_roots,
            "ts": _get_ts(row),
        })
    return out


# ----------------------------
# Plan compilation
# ----------------------------

def select_rows(
    rows: List[Dict[str, Any]],
    roots_hash: Optional[str],
    last_n: Optional[int],
) -> List[Dict[str, Any]]:
    # Filter by roots_hash if given; otherwise keep all.
    if roots_hash:
        rows = [r for r in rows if r.get("roots_hash") == roots_hash]

    # If timestamps exist, sort by ts then stable fallback to original order.
    # If ts missing, keep input order.
    def sort_key(item: Dict[str, Any]) -> Tuple[int, float]:
        ts = item.get("ts")
        return (0 if ts is not None else 1, ts if ts is not None else 0.0)

    # We only sort when there is at least one ts present; otherwise we keep original order.
    if any(r.get("ts") is not None for r in rows):
        rows = sorted(rows, key=sort_key)

    if last_n is not None and last_n >= 0:
        rows = rows[-last_n:]

    return rows


def dedupe_keep_last(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Dedupe by uri, keep the LAST occurrence.
    Maintain the final ordering as the last-seen order.
    """
    last_by_uri: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        last_by_uri[r["uri"]] = r

    # Preserve "last appearance" order:
    seen: set[str] = set()
    out_rev: List[Dict[str, Any]] = []
    for r in reversed(rows):
        uri = r["uri"]
        if uri in seen:
            continue
        seen.add(uri)
        out_rev.append(last_by_uri[uri])
    return list(reversed(out_rev))


def build_steps(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    for r in rows:
        error_code: Optional[str] = None
        if r["decision"] == "DENY":
            # Prefer explicit error_code; otherwise fall back to reason.code; final fallback is stable token.
            error_code = r.get("error_code")
            if not error_code:
                raw = r.get("_raw") or {}
                if isinstance(raw, dict):
                    reason = raw.get("reason")
                    if isinstance(reason, dict) and isinstance(reason.get("code"), str):
                        error_code = reason["code"]
            if not error_code:
                error_code = "DENY_UNKNOWN"
        exp = Expect(decision=r["decision"], error_code=error_code)
        step = Step(uri=r["uri"], expect=exp)
        steps.append({
            "uri": step.uri,
            "expect": {
                "decision": step.expect.decision,
                **({"error_code": step.expect.error_code} if step.expect.error_code else {}),
            }
        })
    return steps


def compile_plan(
    in_path: Path,
    out_path: Path,
    roots_hash: Optional[str],
    last_n: Optional[int],
) -> Dict[str, Any]:
    raw_rows = read_jsonl(in_path)
    rows = normalize_log_rows(raw_rows)
    # Track latest policy roots hash / allowed_roots before filtering.
    latest_roots_hash = next((r["roots_hash"] for r in reversed(rows) if r.get("roots_hash")), None)
    latest_allowed_roots = next((r["allowed_roots"] for r in reversed(rows) if r.get("allowed_roots")), None)
    rows = select_rows(rows, roots_hash=roots_hash, last_n=last_n)
    rows = dedupe_keep_last(rows)
    steps = build_steps(rows)

    plan_roots_hash = roots_hash or latest_roots_hash

    plan = Plan(
        schema_version="mcp07.plan.v1",
        source={
            "kind": "mcp05_policy_decisions.jsonl",
            "path": str(in_path),
            "filters": {
                **({"roots_hash": roots_hash} if roots_hash else {}),
                **({"last_n": last_n} if last_n is not None else {}),
                "dedupe": "uri_keep_last",
            },
        },
        roots_hash=plan_roots_hash,
        steps=steps,
    )

    payload = {
        "schema_version": plan.schema_version,
        "source": plan.source,
        **({"roots_hash": plan.roots_hash} if plan.roots_hash else {}),
        **({"allowed_roots": latest_allowed_roots} if latest_allowed_roots else {}),
        "steps": plan.steps,
    }
    write_json(out_path, payload)
    return payload


# ----------------------------
# CLI
# ----------------------------

def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mcp07-plan-from-log", description="Compile policy decision JSONL into replay plan JSON.")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build-plan", help="Build a replay plan from policy decision logs.")
    b.add_argument("--in", dest="in_path", required=True, help="Input JSONL path, e.g. runtime_data/mcp05_policy_decisions.jsonl")
    b.add_argument("--out", dest="out_path", required=True, help="Output plan JSON path, e.g. runtime_data/mcp07_plan.json")
    b.add_argument("--roots-hash", dest="roots_hash", default=None, help="Filter logs by roots_hash.")
    b.add_argument("--last-n", dest="last_n", type=int, default=None, help="Take last N matched rows before dedupe.")
    return p


def main() -> int:
    args = make_parser().parse_args()

    if args.cmd == "build-plan":
        in_path = Path(args.in_path)
        out_path = Path(args.out_path)
        compile_plan(in_path=in_path, out_path=out_path, roots_hash=args.roots_hash, last_n=args.last_n)
        print(f"✅ wrote plan: {out_path}")
        return 0

    raise RuntimeError(f"Unknown cmd: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
