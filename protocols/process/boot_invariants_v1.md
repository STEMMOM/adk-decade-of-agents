# Boot Invariants v1

**Status:** Stable  
**Scope:** `system.boot` / `system.shutdown` events  
**Principle (Red-Line):** A system only "exists in time" if its birth and death are recorded as verifiable, closed-chain events.

## Invariants

For every `system.boot` and its matching `system.shutdown` (same `trace_id`), the following MUST hold:

1) **Identity fields are present (payload-level)**
- `payload.system_id` MUST exist and be non-empty
- `payload.process_id` MUST exist and be non-empty
- `payload.run_id` MUST exist and be non-empty

2) **Trace is run identity**
- `trace_id` MUST exist and MUST equal `payload.run_id`

3) **Session is never unknown**
- `session_id` MUST exist and MUST NOT be `"unknown"`
  - Recommended sessions: `system`, `p00-startup`, `runtime`, etc.

4) **Runtime actor is visible**
- `payload.actor` or `payload._actor` MUST exist (P00 minimal responsibility anchor)
  - Note: Envelope-level `actor` is enforced in P01; P00 only requires runtime identity is visible at all.

## Closure Requirement

A `system.boot` MUST have a corresponding `system.shutdown` with the same `trace_id`.
If a shutdown is missing, the run is considered institutionally incomplete and replay may be ambiguous.

## Compliance

The repository MUST include an executable test that enforces these invariants against the events ledger:
- `tests/test_p00_boot_invariants.py`
