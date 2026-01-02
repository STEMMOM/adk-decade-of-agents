#!/usr/bin/env python3
"""
MCP-06 — Replay Runner (stdio)

What it does:
- Reads a replay plan (JSON)
- Spawns a target MCP resource server (default: MCP-05)
- Replays reads in order
- Writes a replay report (JSON)
- Optionally diffs with a baseline report and exits non-zero on changes

Usage:
  # 1) create a starter plan
  python projects/mcp/06-replay-runner/main.py init-plan --out runtime_data/mcp06_replay_plan.json

  # 2) run replay (default server: MCP-05)
  python projects/mcp/06-replay-runner/main.py run --plan runtime_data/mcp06_replay_plan.json --out runtime_data/mcp06_replay_report.json

  # 3) run + diff
  python projects/mcp/06-replay-runner/main.py run --plan runtime_data/mcp06_replay_plan.json --out runtime_data/mcp06_replay_report.json \
    --baseline runtime_data/mcp06_baseline_report.json --fail-on-diff
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote


PLAN_SCHEMA = "mcp-replay-plan/v1"
REPORT_SCHEMA = "mcp-replay-report/v1"
DIFF_SCHEMA = "mcp-replay-diff/v1"


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root_from_here() -> Path:
    # .../projects/mcp/06-replay-runner/main.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def default_target_server_script(repo_root: Path) -> Path:
    # default: MCP-05 server
    return repo_root / "projects" / "mcp" / "05-policy-log" / "main.py"


def encode_path(rel: str) -> str:
    # encoded-path contract: {path} is single URI segment, so encode '/' into %2F
    return quote(rel, safe="")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, obj: dict) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def try_parse_json_text(text: str) -> Optional[dict]:
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


@dataclass
class ReplayStep:
    uri: str
    expect_decision: Optional[str] = None  # "ALLOW" or "DENY" (optional)
    expect_error_code: Optional[str] = None


def load_plan(plan_path: Path) -> Tuple[dict, List[ReplayStep]]:
    plan = load_json(plan_path)
    if plan.get("schema") != PLAN_SCHEMA:
        raise ValueError(f"plan.schema must be {PLAN_SCHEMA}")

    steps_in = plan.get("steps", [])
    if not isinstance(steps_in, list) or not steps_in:
        raise ValueError("plan.steps must be a non-empty list")

    steps: List[ReplayStep] = []
    for i, s in enumerate(steps_in):
        if not isinstance(s, dict) or "uri" not in s:
            raise ValueError(f"invalid step[{i}] (must be object with uri)")
        steps.append(
            ReplayStep(
                uri=str(s["uri"]),
                expect_decision=(s.get("expect") or {}).get("decision"),
                expect_error_code=(s.get("expect") or {}).get("error_code"),
            )
        )
    return plan, steps


def starter_plan(repo_root: Path) -> dict:
    # Default: one allowed (under projects/mcp) + one forbidden (repo root)
    rel_ok = "projects/mcp/05-policy-log/main.py"
    rel_bad = ".gitignore"

    ok_uri = f"mcpfs://repo/file/{encode_path(rel_ok)}"
    bad_uri = f"mcpfs://repo/file/{encode_path(rel_bad)}"

    return {
        "schema": PLAN_SCHEMA,
        "generated_at": utc_iso(),
        "notes": "Starter plan. Uses encoded-path contract: {path} is one URI segment (encode '/' as %2F).",
        "steps": [
            {"uri": ok_uri, "expect": {"decision": "ALLOW"}},
            {"uri": bad_uri, "expect": {"decision": "DENY", "error_code": "FORBIDDEN"}},
        ],
    }


def normalize_decision_from_read(maybe_json: Optional[dict], raw_text: str) -> Tuple[str, bool, Optional[str]]:
    """
    Returns: (decision, ok, error_code)

    - If response text is JSON with {"ok": false, "error": {"code": ...}} -> DENY
    - Otherwise treat as allowed text -> ALLOW
    """
    if isinstance(maybe_json, dict) and maybe_json.get("ok") is False:
        code = None
        err = maybe_json.get("error")
        if isinstance(err, dict):
            code = err.get("code")
        return "DENY", False, str(code) if code is not None else None

    # Otherwise: we assume allowed content (text or JSON that isn't the deny envelope)
    return "ALLOW", True, None


def diff_reports(baseline: dict, current: dict) -> dict:
    """
    Minimal diff: compares per-step decision + error_code.
    """
    out = {
        "schema": DIFF_SCHEMA,
        "generated_at": utc_iso(),
        "summary": {"changed": 0, "added": 0, "removed": 0},
        "changes": [],
    }

    b_steps = baseline.get("steps", [])
    c_steps = current.get("steps", [])
    b_map = {s.get("uri"): s for s in b_steps if isinstance(s, dict) and "uri" in s}
    c_map = {s.get("uri"): s for s in c_steps if isinstance(s, dict) and "uri" in s}

    b_uris = set(b_map.keys())
    c_uris = set(c_map.keys())

    added = sorted(list(c_uris - b_uris))
    removed = sorted(list(b_uris - c_uris))
    common = sorted(list(b_uris & c_uris))

    for u in added:
        out["changes"].append({"type": "ADDED", "uri": u, "current": c_map[u]})
    for u in removed:
        out["changes"].append({"type": "REMOVED", "uri": u, "baseline": b_map[u]})

    def key_fields(s: dict) -> Tuple[Any, Any]:
        return (s.get("decision"), s.get("error_code"))

    for u in common:
        b = b_map[u]
        c = c_map[u]
        if key_fields(b) != key_fields(c):
            out["changes"].append(
                {"type": "CHANGED", "uri": u, "baseline": {"decision": b.get("decision"), "error_code": b.get("error_code")},
                 "current": {"decision": c.get("decision"), "error_code": c.get("error_code")}}
            )

    out["summary"]["added"] = len(added)
    out["summary"]["removed"] = len(removed)
    out["summary"]["changed"] = sum(1 for ch in out["changes"] if ch["type"] == "CHANGED")
    return out


async def run_replay(
    *,
    server_script: Path,
    plan_path: Path,
    out_path: Path,
    env: Optional[dict] = None,
) -> dict:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    plan, steps = load_plan(plan_path)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script), "server"],
        env=env or os.environ.copy(),
    )

    report: dict = {
        "schema": REPORT_SCHEMA,
        "generated_at": utc_iso(),
        "plan_path": str(plan_path),
        "server_script": str(server_script),
        "policy": None,
        "steps": [],
        "stats": {"total": 0, "allow": 0, "deny": 0, "mismatch": 0},
    }

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Read policy if available (MCP-04/05 provide it)
            try:
                pol = await session.read_resource("mcpfs://repo/policy")
                pol_text = pol.contents[0].text or ""
                pol_json = try_parse_json_text(pol_text)
                report["policy"] = pol_json or {"raw": pol_text[:500]}
            except Exception as e:
                report["policy"] = {"error": str(e)}

            for idx, st in enumerate(steps):
                rr = await session.read_resource(st.uri)
                text = rr.contents[0].text or ""
                parsed = try_parse_json_text(text)
                decision, ok, error_code = normalize_decision_from_read(parsed, text)

                expect = plan.get("steps", [])[idx].get("expect", {}) if isinstance(plan.get("steps", []), list) else {}
                expect_decision = st.expect_decision
                expect_error = st.expect_error_code

                mismatch = False
                if expect_decision and expect_decision != decision:
                    mismatch = True
                if expect_error and (expect_error != (error_code or "")):
                    mismatch = True

                step_rec = {
                    "i": idx,
                    "uri": st.uri,
                    "decision": decision,
                    "ok": ok,
                    "error_code": error_code,
                    "bytes": len(text.encode("utf-8")),
                    "preview": (text[:120].replace("\n", " ") if text else ""),
                    "expect": expect if expect else None,
                    "mismatch": mismatch,
                }
                report["steps"].append(step_rec)

    # stats
    report["stats"]["total"] = len(report["steps"])
    report["stats"]["allow"] = sum(1 for s in report["steps"] if s["decision"] == "ALLOW")
    report["stats"]["deny"] = sum(1 for s in report["steps"] if s["decision"] == "DENY")
    report["stats"]["mismatch"] = sum(1 for s in report["steps"] if s.get("mismatch"))

    dump_json(out_path, report)
    return report


def main() -> int:
    repo_root = repo_root_from_here()

    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-plan", help="Create a starter replay plan.")
    p_init.add_argument("--out", required=True, help="Output plan path")

    p_run = sub.add_parser("run", help="Run replay and write report.")
    p_run.add_argument("--plan", required=True, help="Replay plan path")
    p_run.add_argument("--out", required=True, help="Replay report output path")
    p_run.add_argument(
        "--server-script",
        default=str(default_target_server_script(repo_root)),
        help="Target MCP server script to spawn (default: MCP-05).",
    )
    p_run.add_argument("--baseline", default=None, help="Baseline report path (optional).")
    p_run.add_argument("--diff-out", default=None, help="Diff output path (optional).")
    p_run.add_argument("--fail-on-diff", action="store_true", help="Exit non-zero if diff has changes.")

    args = p.parse_args()

    if args.cmd == "init-plan":
        out = Path(args.out)
        dump_json(out, starter_plan(repo_root))
        print(f"[MCP-06] wrote plan: {out}")
        return 0

    # run
    plan_path = Path(args.plan)
    out_path = Path(args.out)
    server_script = Path(args.server_script)

    report = asyncio.run(run_replay(server_script=server_script, plan_path=plan_path, out_path=out_path))
    print(f"[MCP-06] wrote report: {out_path} (mismatch={report['stats']['mismatch']})")

    if args.baseline:
        baseline = load_json(Path(args.baseline))
        diff = diff_reports(baseline, report)

        diff_out = Path(args.diff_out) if args.diff_out else out_path.with_suffix(".diff.json")
        dump_json(diff_out, diff)
        print(f"[MCP-06] wrote diff: {diff_out} summary={diff['summary']}")

        has_changes = (diff["summary"]["changed"] + diff["summary"]["added"] + diff["summary"]["removed"]) > 0
        if args.fail_on_diff and has_changes:
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
