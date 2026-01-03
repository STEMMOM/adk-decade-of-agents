# RRB Data Model v1 (Skeleton)

## ReleaseIntent
```json
{
  "actor": "human:alice",
  "repo_ref": "adk-decade-of-agents@main",
  "scope": "season-1",
  "reason": "cut release",
  "timestamp": "2025-12-26T00:00:00Z",
  "inputs": ["plan.md", "test-report.json"],
  "request_hash": "sha256:..."
}
```

## DecisionRecord
```json
{
  "decision_id": "dec_001",
  "intent_hash": "sha256:...",
  "policy_version": "rrb-policy-v1",
  "policy_hash": "sha256:...",
  "decision": "ALLOW",
  "evidence_refs": ["runtime_data/tests/gate-report.json"],
  "timestamp": "2025-12-26T00:05:00Z"
}
```

## OverrideRecord
```json
{
  "override_id": "ovr_001",
  "target_decision_id": "dec_001",
  "by": "human:bob",
  "reason": "accepting risk X",
  "risk_acceptance": "documented",
  "timestamp": "2025-12-26T00:06:00Z",
  "scope": "gate-only"
}
```

## ExecutionRecord
```json
{
  "execution_id": "exe_001",
  "decision_id": "dec_001",
  "action": "tag v1.0",
  "result": "success",
  "timestamp": "2025-12-26T00:07:00Z"
}
```
