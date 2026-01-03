# RRB Constitution v1

- Sovereign boundaries: clear separation between LLM zone and sovereign zone; LLMs cannot self-approve release.  
- Tools may not self-attest legality; human/sovereign approval required.  
- Records are append-only in a history ledger; no mutation, no rewrite.  
- Overrides are additive only; history remains intact.  
- Release Gate: `pytest -q -m gate` must pass; legacy suites are non-blocking but tracked.
