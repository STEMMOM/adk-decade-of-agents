# tools/obs_aggregate_daily.py
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone

def parse_day(ts: str) -> str:
    # expects ISO-8601 with Z
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).date().isoformat()

def pctile(values, p: float):
    if not values:
        return None
    vs = sorted(values)
    k = int(round((p/100.0) * (len(vs)-1)))
    k = max(0, min(k, len(vs)-1))
    return vs[k]

def stats(values):
    if not values:
        return {"count":0,"min":None,"max":None,"p50":None,"p95":None,"mean":None}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "p50": pctile(values, 50),
        "p95": pctile(values, 95),
        "mean": sum(values)/len(values),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True, help="path to observability_events.jsonl")
    ap.add_argument("--day", required=True, help="YYYY-MM-DD (UTC day)")
    ap.add_argument("--out", required=True, help="output daily_metrics_summary.json")
    args = ap.parse_args()

    runs_started = set()
    runs_finished = {}  # run_id -> status
    errors_by_layer = defaultdict(int)
    errors_by_type = defaultdict(int)

    tool_calls_by_name = defaultdict(lambda: {"total":0,"success":0,"error":0})
    tool_lat_all = []
    tool_lat_by_name = defaultdict(list)

    policy_decisions = defaultdict(int)  # allow/block - optional; may be absent
    policy_checks_total = 0
    policy_lat_all = []

    mem_proposed = 0
    mem_committed = 0
    mem_blocked = 0
    mem_by_zone = defaultdict(lambda: {"proposed":0,"committed":0,"blocked":0})
    mem_block_reasons = defaultdict(int)

    run_t0 = {}
    run_total_ms = []

    with open(args.events, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ev = json.loads(line)
            if parse_day(ev["timestamp"]) != args.day:
                continue

            et = ev.get("event_type")
            rid = ev.get("run_id")

            if et == "run_started":
                runs_started.add(rid)
                run_t0[rid] = ev["timestamp"]

            elif et == "run_finished":
                runs_finished[rid] = ev.get("status","unknown")
                # run_total_ms is best derived from timestamps; minimal: use latency_ms if you emit it.
                # Here we approximate by difference of parsed timestamps if both exist.
                if rid in run_t0:
                    t0 = datetime.fromisoformat(run_t0[rid].replace("Z","+00:00"))
                    t1 = datetime.fromisoformat(ev["timestamp"].replace("Z","+00:00"))
                    run_total_ms.append(int((t1 - t0).total_seconds() * 1000))

            elif et == "error_raised":
                layer = ev.get("layer","unknown")
                errors_by_layer[layer] += 1
                errors_by_type[ev.get("error_type","unknown")] += 1

            elif et == "tool_call_finished":
                name = ev.get("tool_name","unknown")
                tool_calls_by_name[name]["total"] += 1
                st = ev.get("status","success")
                if st == "success":
                    tool_calls_by_name[name]["success"] += 1
                else:
                    tool_calls_by_name[name]["error"] += 1
                lat = ev.get("latency_ms")
                if isinstance(lat, int):
                    tool_lat_all.append(lat)
                    tool_lat_by_name[name].append(lat)

            elif et == "policy_check_finished":
                policy_checks_total += 1
                # decision may or may not exist in minimal events
                dec = ev.get("decision")
                if dec in ("allow","block"):
                    policy_decisions[dec] += 1
                lat = ev.get("latency_ms")
                if isinstance(lat, int):
                    policy_lat_all.append(lat)

            elif et == "memory_write_proposed":
                mem_proposed += 1
                zone = ev.get("memory_zone","unknown")
                mem_by_zone[zone]["proposed"] += 1

            elif et == "memory_write_committed":
                mem_committed += 1
                # zone not guaranteed on finished events; keep minimal
                # if you want, include memory_zone also on committed/blocked events.

            elif et == "memory_write_blocked":
                mem_blocked += 1
                reason = ev.get("reason","unknown")
                mem_block_reasons[reason] += 1

    runs_by_status = defaultdict(int)
    for _, st in runs_finished.items():
        runs_by_status[st] += 1

    summary = {
        "schema": "observability.daily_metrics_summary.v1",
        "day": args.day,
        "timezone": "UTC",
        "source": {
            "event_log": args.events,
            "aggregator_version": "obs-agg-v1",
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        },
        "run_summary": {
            "runs_total": len(runs_started),
            "runs_by_status": dict(runs_by_status),
            "errors_total": sum(errors_by_layer.values()),
            "errors_by_layer": dict(errors_by_layer),
            "errors_by_type": dict(errors_by_type),
        },
        "tooling": {
            "tool_calls_total": sum(v["total"] for v in tool_calls_by_name.values()),
            "tool_calls_by_name": dict(tool_calls_by_name),
            "tool_latency_ms": {
                "overall": stats(tool_lat_all),
                "by_tool": {k: stats(v) for k, v in tool_lat_by_name.items()},
            },
        },
        "policy": {
            "policy_checks_total": policy_checks_total,
            "policy_decisions": dict(policy_decisions),
            "policy_latency_ms": stats(policy_lat_all),
        },
        "memory": {
            "memory_write_proposed_total": mem_proposed,
            "memory_write_committed_total": mem_committed,
            "memory_write_blocked_total": mem_blocked,
            "memory_writes_by_zone": dict(mem_by_zone),
            "memory_block_reasons": dict(mem_block_reasons),
        },
        "latency": {
            "run_total_ms": stats(run_total_ms),
        },
        "tokens_and_cost": {
            "token_estimate": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                              "notes": "minimal v1: token tracking not wired"},
            "cost_estimate_usd": {"total": 0, "by_tool": {},
                                 "notes": "minimal v1: cost tracking not wired"},
        }
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
