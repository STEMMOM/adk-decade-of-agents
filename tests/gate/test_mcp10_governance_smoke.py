# tests/test_mcp10_governance_smoke.py
#
# MCP-10 Smoke: DENY (REQUIRE_OVERRIDE) -> OVERRIDDEN evidence chain
#
# Assumptions:
# - projects/mcp/10-governance-layer/main.py PolicyV0 is configured so that
#   fs.read_file returns REQUIRE_OVERRIDE by default, e.g.:
#     PolicyV0.POLICY_SPEC["require_override_tools"] includes "fs.read_file"
# - MCP-09 registry exists at runtime_data/mcp09_registry.json and points to
#   working downstream mock servers (fs + policy).
#
# This test:
# 1) starts MCP-10 server (stdio JSON-RPC)
# 2) calls fs.read_file -> expects 401 Override required
# 3) appends override record (scope tool read_file)
# 4) calls fs.read_file again -> expects success
# 5) asserts decision log contains:
#    - a blocked record under policy_hash X
#    - an OVERRIDDEN record under same policy_hash X with override evidence

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

JSON = Dict[str, Any]


class JsonRpcClientProc:
    def __init__(self, cmd: list[str], env: Optional[dict[str, str]] = None) -> None:
        e = os.environ.copy()
        if env:
            e.update(env)
        self.p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=e,
            bufsize=1,
        )
        assert self.p.stdin and self.p.stdout and self.p.stderr
        self._id = 1

    def call(self, method: str, params: Optional[JSON] = None, timeout_s: float = 6.0) -> JSON:
        rid = self._id
        self._id += 1
        req: JSON = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            req["params"] = params
        self.p.stdin.write(json.dumps(req) + "\n")
        self.p.stdin.flush()

        start = time.time()
        while True:
            if time.time() - start > timeout_s:
                raise TimeoutError(f"timeout waiting for response to id={rid}")
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("server closed stdout")
            resp = json.loads(line)
            if resp.get("id") == rid:
                return resp

    def close(self) -> None:
        try:
            if self.p.poll() is None:
                self.p.terminate()
        except Exception:
            pass


def _append_jsonl(path: Path, obj: JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[JSON]:
    if not path.exists():
        return []
    out: list[JSON] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


@pytest.fixture
def tmp_runtime(tmp_path: Path) -> dict[str, Path]:
    rt = tmp_path / "runtime_data"
    rt.mkdir(parents=True, exist_ok=True)
    return {
        "overrides": rt / "mcp10_overrides.jsonl",
        "decisions": rt / "mcp10_bus_decisions.jsonl",
    }


@pytest.fixture
def gov_proc(tmp_runtime: dict[str, Path]) -> JsonRpcClientProc:
    cmd = ["python", "-m", "projects.mcp.10-governance-layer.main"]
    env = {
        # Use the repo's MCP-09 registry (downstream mock fs/policy servers)
        "MCP10_REGISTRY": "runtime_data/mcp09_registry.json",
        # Isolate override/decision logs in tmpdir
        "MCP10_OVERRIDES": str(tmp_runtime["overrides"]),
        "MCP10_DECISIONS": str(tmp_runtime["decisions"]),
    }
    proc = JsonRpcClientProc(cmd, env=env)
    yield proc
    proc.close()


def test_mcp10_deny_then_overridden(gov_proc: JsonRpcClientProc, tmp_runtime: dict[str, Path]) -> None:
    decisions_path = tmp_runtime["decisions"]
    overrides_path = tmp_runtime["overrides"]

    # Sanity: tools/list should work
    tl = gov_proc.call("tools/list", {})
    assert "result" in tl, tl
    tool_names = [t["name"] for t in tl["result"]["tools"]]
    assert "fs.read_file" in tool_names, tool_names

    # 1) First call should be blocked with "Override required"
    r1 = gov_proc.call("tools/call", {"name": "fs.read_file", "args": {"path": "README.md"}})
    assert "error" in r1, r1
    assert r1["error"]["code"] == 401, r1
    policy = (r1["error"].get("data") or {}).get("policy") or {}
    assert policy.get("decision") == "REQUIRE_OVERRIDE", policy
    policy_hash = policy.get("policy_hash")
    assert isinstance(policy_hash, str) and len(policy_hash) == 64

    # Decision log must exist and contain a blocked record for this policy_hash
    records = _read_jsonl(decisions_path)
    assert records, "decision log should not be empty after first blocked call"
    blocked = [rec for rec in records if rec.get("outcome") == "blocked" and rec.get("policy_hash") == policy_hash]
    assert blocked, records
    assert blocked[-1].get("decision") == "DENY"
    assert blocked[-1].get("request_summary", {}).get("name") == "fs.read_file"

    # 2) Append an override that matches scope (namespace=fs, tool=read_file)
    _append_jsonl(overrides_path, {
        "override_id": "ovr_test_0001",
        "who": "human:test",
        "reason": "test override for fs.read_file",
        "scope": {"namespace": "fs", "tool": "read_file"},
        "expires_at": "2030-01-01T00:00:00Z",
        "created_at": "2025-12-26T00:00:00Z",
    })

    # 3) Second call should pass and read file content
    r2 = gov_proc.call("tools/call", {"name": "fs.read_file", "args": {"path": "README.md"}})
    assert "result" in r2, r2
    assert isinstance(r2["result"].get("content"), str)
    assert "ADK Decade of Agents" in r2["result"]["content"]

    # 4) Decision log should now contain an OVERRIDDEN record with override evidence
    records2 = _read_jsonl(decisions_path)
    overridden = [rec for rec in records2 if rec.get("decision") == "OVERRIDDEN" and rec.get("policy_hash") == policy_hash]
    assert overridden, records2
    last = overridden[-1]
    assert last.get("override_id") == "ovr_test_0001"
    assert last.get("override_who") == "human:test"
    assert last.get("override_reason") == "test override for fs.read_file"
    assert last.get("outcome") == "forwarded"
    assert last.get("request_summary", {}).get("name") == "fs.read_file"
