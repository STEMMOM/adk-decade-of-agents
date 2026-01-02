#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

def read_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))

def write_json(p: Path, obj: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def plan_roots_hash(plan: Dict[str, Any]) -> str | None:
    # Prefer explicit plan.roots_hash; else try plan.source.filters.roots_hash
    if isinstance(plan.get("roots_hash"), str):
        return plan["roots_hash"]
    src = plan.get("source") or {}
    if isinstance(src, dict):
        filters = src.get("filters") or {}
        if isinstance(filters, dict) and isinstance(filters.get("roots_hash"), str):
            return filters["roots_hash"]
    return None


def plan_allowed_roots(plan: Dict[str, Any]) -> List[str] | None:
    if isinstance(plan.get("allowed_roots"), list) and all(isinstance(x, str) for x in plan["allowed_roots"]):
        return plan["allowed_roots"]
    src = plan.get("source") or {}
    if isinstance(src, dict):
        policy = src.get("policy")
        if isinstance(policy, dict):
            ar = policy.get("allowed_roots")
            if isinstance(ar, list) and all(isinstance(x, str) for x in ar):
                return ar
    return None

def step_key(step: Dict[str, Any]) -> str:
    return str(step.get("uri"))

def snapshot(plan_path: Path, out_path: Path) -> None:
    plan = read_json(plan_path)
    allowed_roots = plan_allowed_roots(plan)
    baseline = {
        "schema_version": "mcp08.baseline.v1",
        "plan_schema_version": plan.get("schema_version"),
        "plan_roots_hash": plan_roots_hash(plan),
        **({"plan_allowed_roots": allowed_roots} if allowed_roots else {}),
        "plan_path": str(plan_path),
        # Baseline is FACTS ONLY: store observed steps as-is.
        "steps": plan.get("steps", []),
    }
    write_json(out_path, baseline)
    print(f"✅ wrote baseline: {out_path}")

def diff_steps(plan_steps: List[Dict[str, Any]], base_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    pmap = {step_key(s): s for s in plan_steps}
    bmap = {step_key(s): s for s in base_steps}

    added = [k for k in pmap.keys() if k not in bmap]
    removed = [k for k in bmap.keys() if k not in pmap]
    changed = []
    for k in pmap.keys():
        if k in bmap and pmap[k] != bmap[k]:
            changed.append(k)

    return {"added": added, "removed": removed, "changed": changed}

def check(plan_path: Path, baseline_path: Path, fail_on_diff: bool, enforce_expect: bool) -> int:
    plan = read_json(plan_path)
    base = read_json(baseline_path)

    plan_steps = plan.get("steps", []) or []
    base_steps = base.get("steps", []) or []

    d = diff_steps(plan_steps, base_steps)

    # Roots attribution summary (first glance)
    plan_rh = plan_roots_hash(plan)
    base_rh = base.get("plan_roots_hash")
    roots_changed = (plan_rh is not None and base_rh is not None and plan_rh != base_rh)
    plan_ar = plan_allowed_roots(plan)
    base_ar = base.get("plan_allowed_roots")
    allowed_changed = (plan_ar is not None and base_ar is not None and plan_ar != base_ar)

    summary = {
        "plan_roots_hash": plan_rh,
        "baseline_roots_hash": base_rh,
        "roots_hash_changed": roots_changed,
        "plan_allowed_roots": plan_ar,
        "baseline_allowed_roots": base_ar,
        "allowed_roots_changed": allowed_changed,
        "diff": {
            "added": len(d["added"]),
            "removed": len(d["removed"]),
            "changed": len(d["changed"]),
        },
        "diff_keys": d,
    }
    if roots_changed or allowed_changed:
        summary["attribution"] = "POLICY_CHANGED"
    elif any(summary["diff"][k] > 0 for k in ("added", "removed", "changed")):
        summary["attribution"] = "IMPLEMENTATION_CHANGED"
    else:
        summary["attribution"] = "NO_CHANGE"

    # Enforce expect only when explicitly asked
    expect_failures: List[Dict[str, Any]] = []
    if enforce_expect:
        for s in plan_steps:
            exp = (s.get("expect") or {}) if isinstance(s.get("expect"), dict) else {}
            dec = exp.get("decision")
            if dec not in ("ALLOW", "DENY"):
                continue
            # baseline is facts snapshot; so "enforce expect" means: plan step must match baseline step exactly.
            # (You can later upgrade this to compare against replay outcomes.)
            uri = step_key(s)
            b = next((x for x in base_steps if step_key(x) == uri), None)
            if b is None:
                expect_failures.append({"uri": uri, "reason": "missing_in_baseline"})
            elif b.get("expect") != s.get("expect"):
                expect_failures.append({"uri": uri, "reason": "expect_mismatch", "plan": s.get("expect"), "baseline": b.get("expect")})

    summary["enforce_expect"] = enforce_expect
    summary["expect_failures"] = expect_failures

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    has_diff = any(summary["diff"][k] > 0 for k in ("added", "removed", "changed"))
    has_expect_fail = len(expect_failures) > 0

    if fail_on_diff and (has_diff or (enforce_expect and has_expect_fail)):
        return 2
    return 0

def main() -> int:
    p = argparse.ArgumentParser(prog="mcp08-baseline-manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("snapshot", help="Create a baseline snapshot (facts only).")
    s.add_argument("--plan", required=True)
    s.add_argument("--out", required=True)

    c = sub.add_parser("check", help="Diff plan vs baseline with attribution.")
    c.add_argument("--plan", required=True)
    c.add_argument("--baseline", required=True)
    c.add_argument("--fail-on-diff", action="store_true")
    c.add_argument("--enforce-expect", action="store_true")

    f = sub.add_parser("smoke-roots-flip", help="Append a synthetic policy decision to simulate roots change.")
    f.add_argument("--log", required=True, help="Path to mcp05_policy_decisions.jsonl")

    args = p.parse_args()

    if args.cmd == "snapshot":
        snapshot(Path(args.plan), Path(args.out))
        return 0
    if args.cmd == "check":
        return check(Path(args.plan), Path(args.baseline), args.fail_on_diff, args.enforce_expect)
    if args.cmd == "smoke-roots-flip":
        log_path = Path(args.log)
        record = {
            "decision": "ALLOW",
            "uri": "mcpfs://repo/file/docs%2FENVIRONMENT.md",
            "reason": {"code": "OK"},
            "policy": {
                "allowed_roots": ["projects/mcp", "docs"],
                "roots_hash": "937c59508db97f7d6fd2d225de4acb5e0ec5414a7ef74fd3a80da3403f527e1f",
            },
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).timestamp(),
        }
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fobj:
            fobj.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"✅ appended synthetic policy roots flip to {log_path}")
        return 0

    return 1

if __name__ == "__main__":
    raise SystemExit(main())
