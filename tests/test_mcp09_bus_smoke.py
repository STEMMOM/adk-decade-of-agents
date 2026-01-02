# tests/test_mcp09_bus_smoke.py

from __future__ import annotations
import json
import os
import subprocess
import time
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

    def call(self, method: str, params: Optional[JSON] = None) -> JSON:
        rid = self._id
        self._id += 1
        req: JSON = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            req["params"] = params
        self.p.stdin.write(json.dumps(req) + "\n")
        self.p.stdin.flush()

        # read until matching id
        start = time.time()
        while True:
            if time.time() - start > 5:
                raise TimeoutError("timeout waiting for response")
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("bus closed stdout")
            resp = json.loads(line)
            if resp.get("id") == rid:
                return resp

    def close(self) -> None:
        try:
            if self.p.poll() is None:
                self.p.terminate()
        except Exception:
            pass


@pytest.fixture
def bus_proc() -> JsonRpcClientProc:
    # run bus as module; adjust if your repo doesn't support it
    cmd = ["python", "-m", "projects.mcp.09-capability-bus.main"]
    env = {"MCP09_REGISTRY": "runtime_data/mcp09_registry.json"}
    proc = JsonRpcClientProc(cmd, env=env)
    yield proc
    proc.close()


def test_tools_list_has_two_namespaces(bus_proc: JsonRpcClientProc) -> None:
    resp = bus_proc.call("tools/list", {})
    assert "result" in resp, resp
    tools = resp["result"]["tools"]
    names = [t["name"] for t in tools]

    # invariant #1: namespace required
    assert any(n.startswith("fs.") for n in names), names
    assert any(n.startswith("policy.") for n in names), names

    # not allow non-namespaced
    assert all("." in n for n in names), names


def test_tools_call_routes_to_downstream(bus_proc: JsonRpcClientProc) -> None:
    resp = bus_proc.call("tools/call", {"name": "policy.evaluate", "args": {"action": "read_something"}})
    assert "result" in resp, resp
    assert resp["result"]["decision"] in ("ALLOW", "DENY")


def test_downstream_error_not_swallowed(bus_proc: JsonRpcClientProc) -> None:
    # this triggers mock_fs_server forced error
    resp = bus_proc.call("tools/call", {"name": "fs.read_file", "args": {"path": "__error__"}})
    assert "error" in resp, resp

    data = resp["error"].get("data") or {}
    assert data.get("source_server") == "fs", data
    # error code/message preserved (transparent)
    assert resp["error"]["code"] == 1234
