#!/usr/bin/env python3
# projects/mcp/10-governance-layer/main.py
#
# MCP-10 Governance Layer (minimal skeleton)
# - Wraps a Capability Bus (MCP-09 style) with:
#   1) policy.evaluate(request_summary) -> ALLOW / DENY / REQUIRE_OVERRIDE
#   2) override JSONL (who/why/scope/expires_at) as auditable exception channel
#   3) decision log JSONL for every request (tool/resource)
#
# Protocol: JSON-RPC 2.0 over stdio, one JSON per line (stdout is protocol; logs must be stderr)

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

JSON = Dict[str, Any]


# ---------------------------
# Utilities
# ---------------------------

def _eprint(*args: Any) -> None:
    print(*args, file=sys.stderr, flush=True)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _stable_hash(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(b)


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


def _append_jsonl(path: Path, obj: JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _parse_iso_z(s: str) -> Optional[datetime]:
    # Accept "2025-01-01T00:00:00Z" or ISO with offset
    try:
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s)
    except Exception:
        return None


# ---------------------------
# JSON-RPC helpers
# ---------------------------

def _jsonrpc_ok(req_id: Any, result: Any) -> JSON:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _jsonrpc_err(req_id: Any, code: int, message: str, data: Any = None) -> JSON:
    err: JSON = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


# ---------------------------
# Downstream process wrapper (MCP-09 style)
# ---------------------------

@dataclass(frozen=True)
class DownstreamSpec:
    name: str
    command: List[str]
    env: Dict[str, str]


class JsonRpcProcess:
    """
    Minimal JSON-RPC over stdio: one JSON per line.
    Thread-safe request/response with incremental id.

    NOTE: start_new_session=True isolates downstream from terminal Ctrl+C (macOS/Linux),
          so bus can shutdown gracefully without downstream stack trace noise.
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
            start_new_session=True,  # infra patch: isolate downstream from Ctrl+C
        )
        assert self.p.stdin and self.p.stdout and self.p.stderr

        self._lock = threading.Lock()
        self._next_id = 1

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

            while True:
                resp = _read_jsonl_line(self.p.stdout)
                if resp is None:
                    raise RuntimeError(f"Downstream {self.spec.name} closed stdout")
                if resp.get("id") == req_id:
                    return resp

    def close(self) -> None:
        try:
            if self.p.poll() is None:
                # terminate only the downstream process group/session
                try:
                    os.killpg(self.p.pid, signal.SIGTERM)
                except Exception:
                    self.p.terminate()
        except Exception:
            pass


class CapabilityBusV0:
    """
    MCP-09 style aggregation:
      - tools/list aggregates with namespace prefix "ns.tool"
      - tools/call routes by namespace
      - resources/list aggregates with namespace prefix "ns::uri"
      - resources/read routes by namespace
    """
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
        return f"{namespace}::{uri}"

    @staticmethod
    def split_ns_uri(ns_uri: str) -> Tuple[str, str]:
        if "::" not in ns_uri:
            raise ValueError("namespace is required in uri")
        ns, uri = ns_uri.split("::", 1)
        if not ns or not uri:
            raise ValueError("invalid namespaced uri")
        return ns, uri

    def tools_list(self) -> JSON:
        items: List[JSON] = []
        for ns, proc in self.downstreams.items():
            resp = proc.call("tools/list", {})
            if "error" in resp:
                return {"_bus_error_wrapped": True, "error": self._wrap_error(resp["error"], ns)}
            tools = (resp.get("result") or {}).get("tools", []) or []
            for t in tools:
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
            return {"_bus_error_wrapped": True, "error": self._wrap_error(resp["error"], ns)}
        return resp.get("result", {})

    def resources_list(self) -> JSON:
        items: List[JSON] = []
        for ns, proc in self.downstreams.items():
            resp = proc.call("resources/list", {})
            if "error" in resp:
                return {"_bus_error_wrapped": True, "error": self._wrap_error(resp["error"], ns)}
            resources = (resp.get("result") or {}).get("resources", []) or []
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
            return {"_bus_error_wrapped": True, "error": self._wrap_error(resp["error"], ns)}
        return resp.get("result", {})

    @staticmethod
    def _wrap_error(err: JSON, source_server: str) -> JSON:
        e2 = dict(err)
        data = e2.get("data") or {}
        if not isinstance(data, dict):
            data = {"_original_data": data}
        data["source_server"] = source_server
        e2["data"] = data
        return e2

    def close(self) -> None:
        for p in self.downstreams.values():
            try:
                p.close()
            except Exception:
                pass


# ---------------------------
# Policy / Override / Audit
# ---------------------------

class PolicyV0:
    """
    Minimal, deterministic policy:
      - PURE function on request_summary
      - returns (decision, reason)
      - provides policy_version + policy_hash for decision logging

    Replace this later with a real rule engine; keep hash stable across versions.
    """
    POLICY_VERSION = "mcp10-policy-v0"

    # Example defaults:
    # - Deny access to docs resources by default (demonstration)
    # - Require override for any resource read outside allowed namespaces (optional)
    POLICY_SPEC = {
        "deny_resource_uri_contains": ["docs", "/docs", "docs/"],
        "deny_tools": [],  # e.g. ["fs.delete", "shell.exec"]
        "require_override_tools": ["fs.read_file"],  # e.g. ["fs.write_file"]
        "require_override_resource_uri_contains": [],  # e.g. ["secrets"]
    }

    def __init__(self) -> None:
        self.policy_hash = _stable_hash({
            "policy_version": self.POLICY_VERSION,
            "policy_spec": self.POLICY_SPEC,
        })

    def evaluate(self, request_summary: JSON) -> JSON:
        """
        Return:
          {"decision": "...", "reason": "...", "policy_version": "...", "policy_hash": "..."}
        """
        rtype = request_summary.get("type")
        namespace = request_summary.get("namespace")
        name = request_summary.get("name")  # namespaced tool name (ns.tool) OR resource uri (ns::uri)
        uri = request_summary.get("uri") or ""

        # Deny list: tools
        if rtype == "tool":
            if isinstance(name, str) and name in self.POLICY_SPEC.get("deny_tools", []):
                return self._out("DENY", "tool denied by policy")
            if isinstance(name, str) and name in self.POLICY_SPEC.get("require_override_tools", []):
                return self._out("REQUIRE_OVERRIDE", "tool requires override")

        # Deny list: resources
        if rtype == "resource":
            for needle in self.POLICY_SPEC.get("deny_resource_uri_contains", []):
                if needle and needle in uri:
                    return self._out("DENY", "resource uri denied by policy")
            for needle in self.POLICY_SPEC.get("require_override_resource_uri_contains", []):
                if needle and needle in uri:
                    return self._out("REQUIRE_OVERRIDE", "resource requires override")

        # Default allow
        _ = namespace  # reserved for future policy
        return self._out("ALLOW", "default allow")

    def _out(self, decision: str, reason: str) -> JSON:
        return {
            "decision": decision,
            "reason": reason,
            "policy_version": self.POLICY_VERSION,
            "policy_hash": self.policy_hash,
        }


class OverrideStore:
    """
    JSONL store for overrides:
      runtime_data/mcp10_overrides.jsonl

    Each line is a record:
      {
        "override_id": "...uuid...",
        "who": "...",
        "reason": "...",
        "scope": {"namespace": "...", "tool": "read_file"} OR {"namespace": "...", "uri_prefix": "file://..."} ...
        "expires_at": "2025-01-01T00:00:00Z",
        "created_at": "..."
      }
    """
    def __init__(self, path: Path) -> None:
        self.path = path

    def _iter_records(self) -> List[JSON]:
        if not self.path.exists():
            return []
        out: List[JSON] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
        return out

    def find_applicable(self, request_summary: JSON) -> Optional[JSON]:
        now = datetime.now(timezone.utc)
        rtype = request_summary.get("type")
        ns = request_summary.get("namespace")
        tool_full = request_summary.get("name")  # "ns.tool"
        uri_full = request_summary.get("uri")  # "ns::uri"

        for rec in reversed(self._iter_records()):
            exp = _parse_iso_z(str(rec.get("expires_at", "")))
            if exp is None or exp <= now:
                continue

            scope = rec.get("scope") or {}
            if not isinstance(scope, dict):
                continue

            if scope.get("namespace") and scope.get("namespace") != ns:
                continue

            if rtype == "tool":
                # scope may specify full namespaced tool or tool name only
                s_tool = scope.get("tool")  # e.g. "read_file" (preferred) OR "ns.tool"
                if isinstance(s_tool, str):
                    if s_tool == tool_full:
                        return rec
                    # allow specifying tool name without namespace
                    if "." in tool_full and s_tool == tool_full.split(".", 1)[1]:
                        return rec

            if rtype == "resource":
                s_uri_prefix = scope.get("uri_prefix")  # prefix on underlying uri or namespaced uri
                if isinstance(s_uri_prefix, str) and isinstance(uri_full, str):
                    if uri_full.startswith(s_uri_prefix):
                        return rec
                    # allow specifying prefix without namespace (after "ns::")
                    if "::" in uri_full and uri_full.split("::", 1)[1].startswith(s_uri_prefix):
                        return rec

                s_uri = scope.get("uri")  # exact
                if isinstance(s_uri, str) and isinstance(uri_full, str):
                    if uri_full == s_uri:
                        return rec
                    if "::" in uri_full and s_uri == uri_full.split("::", 1)[1]:
                        return rec

        return None


class DecisionLogger:
    """
    Append-only JSONL decision log:
      runtime_data/mcp10_bus_decisions.jsonl
    """
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(
        self,
        *,
        request_summary: JSON,
        decision: str,
        policy_meta: JSON,
        override_rec: Optional[JSON] = None,
        outcome: str,
    ) -> None:
        record: JSON = {
            "decision_id": f"dec_{uuid.uuid4().hex}",
            "timestamp": _utc_now_iso(),
            "request_summary": request_summary,
            "decision": decision,  # ALLOW / DENY / OVERRIDDEN
            "policy_version": policy_meta.get("policy_version"),
            "policy_hash": policy_meta.get("policy_hash"),
            "policy_reason": policy_meta.get("reason"),
            "override_id": override_rec.get("override_id") if override_rec else None,
            "override_who": override_rec.get("who") if override_rec else None,
            "override_reason": override_rec.get("reason") if override_rec else None,
            "outcome": outcome,  # "blocked" | "forwarded" | "invalid_request" | "error"
        }
        _append_jsonl(self.path, record)


# ---------------------------
# Governance Bus (wraps CapabilityBusV0)
# ---------------------------

class GovernanceBus:
    def __init__(
        self,
        *,
        registry_path: str,
        overrides_path: Path,
        decisions_path: Path,
    ) -> None:
        self.bus = CapabilityBusV0(registry_path=registry_path)
        self.policy = PolicyV0()
        self.overrides = OverrideStore(overrides_path)
        self.decisions = DecisionLogger(decisions_path)

    def close(self) -> None:
        self.bus.close()

    @staticmethod
    def _summarize_tool_call(params: JSON) -> JSON:
        # params: {"name": "ns.tool", "args": {...}}
        name = params.get("name")
        if not isinstance(name, str) or "." not in name:
            raise ValueError("namespace is required in tool name")
        ns = name.split(".", 1)[0]
        args = params.get("args") or {}
        return {
            "type": "tool",
            "namespace": ns,
            "name": name,  # keep namespaced name in summary
            "args_hash": _stable_hash(args),
        }

    @staticmethod
    def _summarize_resource_read(params: JSON) -> JSON:
        # params: {"uri": "ns::uri"}
        uri = params.get("uri")
        if not isinstance(uri, str) or "::" not in uri:
            raise ValueError("namespace is required in uri")
        ns = uri.split("::", 1)[0]
        return {
            "type": "resource",
            "namespace": ns,
            "uri": uri,  # keep namespaced uri in summary
        }

    def govern_and_call_tool(self, params: JSON) -> Tuple[Optional[JSON], Optional[JSON]]:
        summary = self._summarize_tool_call(params)
        policy_out = self.policy.evaluate(summary)

        if policy_out["decision"] == "ALLOW":
            self.decisions.write(
                request_summary=summary,
                decision="ALLOW",
                policy_meta=policy_out,
                override_rec=None,
                outcome="forwarded",
            )
            return self.bus.tools_call(params), None

        if policy_out["decision"] == "DENY":
            self.decisions.write(
                request_summary=summary,
                decision="DENY",
                policy_meta=policy_out,
                override_rec=None,
                outcome="blocked",
            )
            return None, _jsonrpc_err(None, 403, "Denied by policy", {"policy": policy_out})

        # REQUIRE_OVERRIDE
        ov = self.overrides.find_applicable(summary)
        if ov:
            self.decisions.write(
                request_summary=summary,
                decision="OVERRIDDEN",
                policy_meta=policy_out,
                override_rec=ov,
                outcome="forwarded",
            )
            return self.bus.tools_call(params), None

        self.decisions.write(
            request_summary=summary,
            decision="DENY",
            policy_meta=policy_out,
            override_rec=None,
            outcome="blocked",
        )
        return None, _jsonrpc_err(None, 401, "Override required", {"policy": policy_out})

    def govern_and_read_resource(self, params: JSON) -> Tuple[Optional[JSON], Optional[JSON]]:
        summary = self._summarize_resource_read(params)
        policy_out = self.policy.evaluate(summary)

        if policy_out["decision"] == "ALLOW":
            self.decisions.write(
                request_summary=summary,
                decision="ALLOW",
                policy_meta=policy_out,
                override_rec=None,
                outcome="forwarded",
            )
            return self.bus.resources_read(params), None

        if policy_out["decision"] == "DENY":
            self.decisions.write(
                request_summary=summary,
                decision="DENY",
                policy_meta=policy_out,
                override_rec=None,
                outcome="blocked",
            )
            return None, _jsonrpc_err(None, 403, "Denied by policy", {"policy": policy_out})

        ov = self.overrides.find_applicable(summary)
        if ov:
            self.decisions.write(
                request_summary=summary,
                decision="OVERRIDDEN",
                policy_meta=policy_out,
                override_rec=ov,
                outcome="forwarded",
            )
            return self.bus.resources_read(params), None

        self.decisions.write(
            request_summary=summary,
            decision="DENY",
            policy_meta=policy_out,
            override_rec=None,
            outcome="blocked",
        )
        return None, _jsonrpc_err(None, 401, "Override required", {"policy": policy_out})


# ---------------------------
# Main: stdio JSON-RPC server
# ---------------------------

def main() -> None:
    registry_path = os.environ.get("MCP10_REGISTRY", os.environ.get("MCP09_REGISTRY", "runtime_data/mcp09_registry.json"))
    overrides_path = Path(os.environ.get("MCP10_OVERRIDES", "runtime_data/mcp10_overrides.jsonl"))
    decisions_path = Path(os.environ.get("MCP10_DECISIONS", "runtime_data/mcp10_bus_decisions.jsonl"))

    gov = GovernanceBus(
        registry_path=registry_path,
        overrides_path=overrides_path,
        decisions_path=decisions_path,
    )

    try:
        for raw in sys.stdin:
            line = raw.strip()
            if not line:
                continue

            req_id = None
            try:
                req = json.loads(line)
                req_id = req.get("id")

                # -------- Patch: -32600 Invalid Request for malformed JSON-RPC --------
                # Missing/invalid "method" is an invalid request (not "method not found").
                method = req.get("method", None)
                if not isinstance(method, str) or not method:
                    # record as invalid_request (optional but helpful for audit cleanliness)
                    gov.decisions.write(
                        request_summary={"type": "invalid", "raw_hash": _sha256_bytes(line.encode("utf-8"))},
                        decision="DENY",
                        policy_meta={"policy_version": gov.policy.POLICY_VERSION, "policy_hash": gov.policy.policy_hash, "reason": "invalid request"},
                        override_rec=None,
                        outcome="invalid_request",
                    )
                    resp = _jsonrpc_err(req_id, -32600, "Invalid Request", {"hint": "missing or invalid 'method'"})
                    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                    sys.stdout.flush()
                    continue
                # --------------------------------------------------------------------

                params = req.get("params") or {}

                # List endpoints (typically safe); still can be governed later if desired.
                if method == "tools/list":
                    out = gov.bus.tools_list()
                    if isinstance(out, dict) and out.get("_bus_error_wrapped"):
                        resp = {"jsonrpc": "2.0", "id": req_id, "error": out["error"]}
                    else:
                        resp = _jsonrpc_ok(req_id, out)

                elif method == "resources/list":
                    out = gov.bus.resources_list()
                    if isinstance(out, dict) and out.get("_bus_error_wrapped"):
                        resp = {"jsonrpc": "2.0", "id": req_id, "error": out["error"]}
                    else:
                        resp = _jsonrpc_ok(req_id, out)

                # Governed endpoints (enforced)
                elif method == "tools/call":
                    result, err_resp = gov.govern_and_call_tool(params)
                    if err_resp is not None:
                        # err_resp has id=None; fix id to caller's id
                        err_resp["id"] = req_id
                        resp = err_resp
                    else:
                        # pass through downstream error wrapping
                        if isinstance(result, dict) and result.get("_bus_error_wrapped"):
                            resp = {"jsonrpc": "2.0", "id": req_id, "error": result["error"]}
                        else:
                            resp = _jsonrpc_ok(req_id, result)

                elif method == "resources/read":
                    result, err_resp = gov.govern_and_read_resource(params)
                    if err_resp is not None:
                        err_resp["id"] = req_id
                        resp = err_resp
                    else:
                        if isinstance(result, dict) and result.get("_bus_error_wrapped"):
                            resp = {"jsonrpc": "2.0", "id": req_id, "error": result["error"]}
                        else:
                            resp = _jsonrpc_ok(req_id, result)

                else:
                    # Valid JSON-RPC but unknown method
                    resp = _jsonrpc_err(req_id, -32601, f"Method not found: {method}")

            except KeyboardInterrupt:
                raise
            except Exception as e:
                resp = _jsonrpc_err(req_id, -32603, "Internal error", {"error": str(e)})

            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

    except KeyboardInterrupt:
        # Graceful shutdown: no stdout output here (stdout is protocol)
        pass
    finally:
        gov.close()


if __name__ == "__main__":
    main()
