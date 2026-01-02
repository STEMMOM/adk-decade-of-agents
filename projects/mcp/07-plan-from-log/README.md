


q

07 — Plan-from-Log

**Goal:** compile `runtime_data/mcp05_policy_decisions.jsonl` into a replay plan JSON.

This makes the pipeline: **behavior evidence (log) → replay plan (plan)** automatic.

## Why

Handwritten plans drift. In a long-term system, regression must be grounded in *what actually happened*.

## Invariants

- Plan is derived ONLY from log (no guessing).
- Each step includes:
  - `uri`
  - `expect.decision` from log (ALLOW / DENY)
  - `expect.error_code` only when DENY (if present)

## Usage

```bash
python -m projects.mcp.07_plan_from_log.main build-plan \
  --in runtime_data/mcp05_policy_decisions.jsonl \
  --out runtime_data/mcp07_plan.json \
  --roots-hash <optional> \
  --last-n 200
