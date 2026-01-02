#!/usr/bin/env python3
# projects/mcp/09-capability-bus/main.py

from __future__ import annotations

import json
import os
import sys
import hashlib
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


JSON = Dict[str, Any]


def _eprint(*args: Any) -> None:
    print(*args, file=sys.stderr, flush=True)


def _stable_hash(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _read_jsonl_line(stream) -> Optional[JSON]:
    line = stream.readline()
    if not line:
        return None
    line = line.strip()
    if not line:
        return None
    return json.loads(line)


def _write_jsonl_line(stream, obj: JSON) -> None:
    stream.write(json.dumps(obj, ensure_ascii=False) + "\n")
    stream.flush()


@dataclass(frozen=True)
class DownstreamSpec:
    name: str
    command: List[str]
    env: Dict[str, str]


class JsonRpcProcess:
    """
    Minimal JSON-RPC over stdio: one JSON per line.
    Thread-safe request/response with incremental id.
    """
    def __init__(self, spec: DownstreamSpec) -> None:
        self.spec = spec
        env = os.environ.copy()
        env.update(spec.env or {})
        self.p = subprocess.Popen(
            spec.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1,
            start_new_session=True,
        )
        assert self.p.stdin and self.p.stdout and self.p.stderr

        self._lock = threading.Lock()
        self._next_id = 1

        # Drain stderr in background so child won't block
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()

    def _drain_stderr(self) -> None:
        assert self.p.stderr
        for line in self.p.stderr:
            _eprint(f"[downstream:{self.spec.name}:stderr] {line.rstrip()}")

    def call(self, method: str, params: Optional[JSON] = None) -> JSON:
        with self._lock:
            req_id = self._next_id
            self._next_id += 1
            req: JSON = {"jsonrpc": "2.0", "id": req_id, "method": method}
            if params is not None:
                req["params"] = params

            assert self.p.stdin and self.p.stdout
            _write_jsonl_line(self.p.stdin, req)

            # Read until matching id
            while True:
                resp = _read_jsonl_line(self.p.stdout)
                if resp is None:
                    raise RuntimeError(f"Downstream {self.spec.name} closed stdout")
                if resp.get("id") == req_id:
                    return resp

    def close(self) -> None:
        try:
            if self.p.poll() is None:
                self.p.terminate()
        except Exception:
            pass


class CapabilityBus:
    def __init__(self, registry_path: str) -> None:
        reg = json.loads(Path(registry_path).read_text(encoding="utf-8"))
        servers = reg.get("servers", [])
        if not isinstance(servers, list) or not servers:
            raise ValueError("registry.servers must be a non-empty list")

        self.downstreams: Dict[str, JsonRpcProcess] = {}
        for s in servers:
            name = s["name"]
            if not name or "." in name:
                raise ValueError(f"invalid namespace name: {name!r}")
            if name in self.downstreams:
                raise ValueError(f"duplicate namespace: {name}")

            cmd = s["command"]
            if not isinstance(cmd, list) or not cmd:
                raise ValueError(f"invalid command for {name}")
            env = s.get("env") or {}
            if not isinstance(env, dict):
                raise ValueError(f"invalid env for {name}")

            self.downstreams[name] = JsonRpcProcess(DownstreamSpec(name=name, command=cmd, env=env))

    # ---- namespace helpers ----
    @staticmethod
    def ns_tool(namespace: str, tool_name: str) -> str:
        return f"{namespace}.{tool_name}"

    @staticmethod
    def split_ns_tool(ns_tool_name: str) -> Tuple[str, str]:
        if "." not in ns_tool_name:
            raise ValueError("namespace is required in tool name")
        ns, tool = ns_tool_name.split(".", 1)
        if not ns or not tool:
            raise ValueError("invalid namespaced tool name")
        return ns, tool

    @staticmethod
    def ns_uri(namespace: str, uri: str) -> str:
        # v0: simple, grep-friendly
        return f"{namespace}::{uri}"

    @staticmethod
    def split_ns_uri(ns_uri: str) -> Tuple[str, str]:
        if "::" not in ns_uri:
            raise ValueError("namespace is required in uri")
        ns, uri = ns_uri.split("::", 1)
        if not ns or not uri:
            raise ValueError("invalid namespaced uri")
        return ns, uri

    # ---- bus methods ----
    def tools_list(self) -> JSON:
        items: List[JSON] = []
        for ns, proc in self.downstreams.items():
            resp = proc.call("tools/list", {})
            if "error" in resp:
                # propagate downstream errors transparently
                return self._wrap_error(resp["error"], source_server=ns)
            result = resp.get("result", {})
            tools = result.get("tools", [])
            for t in tools:
                # expected t: {"name": "...", ...}
                t2 = dict(t)
                t2["name"] = self.ns_tool(ns, t.get("name", ""))
                items.append(t2)
        return {"tools": items}

    def tools_call(self, params: JSON) -> JSON:
        ns_tool = params.get("name")
        if not isinstance(ns_tool, str):
            raise ValueError("tools/call requires params.name as string")
        ns, tool = self.split_ns_tool(ns_tool)

        proc = self.downstreams.get(ns)
        if proc is None:
            raise ValueError(f"unknown namespace: {ns}")

        forwarded = dict(params)
        forwarded["name"] = tool

        resp = proc.call("tools/call", forwarded)
        if "error" in resp:
            return self._wrap_error(resp["error"], source_server=ns)
        return resp.get("result", {})

    def resources_list(self) -> JSON:
        items: List[JSON] = []
        for ns, proc in self.downstreams.items():
            resp = proc.call("resources/list", {})
            if "error" in resp:
                return self._wrap_error(resp["error"], source_server=ns)
            result = resp.get("result", {})
            resources = result.get("resources", [])
            for r in resources:
                r2 = dict(r)
                r2["uri"] = self.ns_uri(ns, r.get("uri", ""))
                items.append(r2)
        return {"resources": items}

    def resources_read(self, params: JSON) -> JSON:
        ns_uri = params.get("uri")
        if not isinstance(ns_uri, str):
            raise ValueError("resources/read requires params.uri as string")
        ns, uri = self.split_ns_uri(ns_uri)
        proc = self.downstreams.get(ns)
        if proc is None:
            raise ValueError(f"unknown namespace: {ns}")
        forwarded = dict(params)
        forwarded["uri"] = uri
        resp = proc.call("resources/read", forwarded)
        if "error" in resp:
            return self._wrap_error(resp["error"], source_server=ns)
        return resp.get("result", {})

    @staticmethod
    def _wrap_error(err: JSON, source_server: str) -> JSON:
        # invariant #2: bus does NOT swallow errors, returns as-is + source_server
        e2 = dict(err)
        data = e2.get("data") or {}
        if not isinstance(data, dict):
            data = {"_original_data": data}
        data["source_server"] = source_server
        e2["data"] = data
        return {"_bus_error_wrapped": True, "error": e2}


def _jsonrpc_ok(req_id: Any, result: Any) -> JSON:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _jsonrpc_err(req_id: Any, code: int, message: str, data: Any = None) -> JSON:
    err: JSON = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


def main() -> None:
    registry_path = os.environ.get("MCP09_REGISTRY", "runtime_data/mcp09_registry.json")
    bus = CapabilityBus(registry_path=registry_path)

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                req_id = req.get("id")
                method = req.get("method")
                params = req.get("params") or {}
                if not method:
                    resp = _jsonrpc_err(req_id, -32600, "Invalid Request: missing method")
                elif method == "tools/list":
                    out = bus.tools_list()
                    if isinstance(out, dict) and out.get("_bus_error_wrapped"):
                        resp = {"jsonrpc": "2.0", "id": req_id, "error": out["error"]}
                    else:
                        resp = _jsonrpc_ok(req_id, out)

                elif method == "tools/call":
                    out = bus.tools_call(params)
                    if isinstance(out, dict) and out.get("_bus_error_wrapped"):
                        resp = {"jsonrpc": "2.0", "id": req_id, "error": out["error"]}
                    else:
                        resp = _jsonrpc_ok(req_id, out)

                elif method == "resources/list":
                    out = bus.resources_list()
                    if isinstance(out, dict) and out.get("_bus_error_wrapped"):
                        resp = {"jsonrpc": "2.0", "id": req_id, "error": out["error"]}
                    else:
                        resp = _jsonrpc_ok(req_id, out)

                elif method == "resources/read":
                    out = bus.resources_read(params)
                    if isinstance(out, dict) and out.get("_bus_error_wrapped"):
                        resp = {"jsonrpc": "2.0", "id": req_id, "error": out["error"]}
                    else:
                        resp = _jsonrpc_ok(req_id, out)

                else:
                    resp = _jsonrpc_err(req_id, -32601, f"Method not found: {method}")

            except Exception as e:
                resp = _jsonrpc_err(req.get("id") if "req" in locals() else None, -32603, "Internal error", {"error": str(e)})

            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in bus.downstreams.values():
            proc.close()


if __name__ == "__main__":
    main()
