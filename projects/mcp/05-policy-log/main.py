#!/usr/bin/env python3
"""
MCP-05 — Policy Decision Logging for Resources (Roots + Gate + JSONL log)

Run:
  python projects/mcp/05-policy-log/main.py server
  python projects/mcp/05-policy-log/main.py client

Config:
  MCP04_ROOTS="projects/mcp,docs"          (comma-separated, repo-relative; default: projects/mcp)
  MCP05_LOG_PATH="runtime_data/mcp05_policy_decisions.jsonl"  (default)
  MCP05_LOG_ENABLED="1"                    (default: 1; set 0 to disable logging)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote, unquote

POLICY_SCHEMA = "mcp-policy/v1"
DECISION_SCHEMA = "mcp-policy-decision/v1"
INDEX_SCHEMA = "mcpfs-index/v1"
DIR_SCHEMA = "mcpfs-dir/v1"


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root_from_here() -> Path:
    # .../projects/mcp/05-policy-log/main.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def normalize_root(r: str) -> str:
    r = (r or "").strip().replace("\\", "/")
    while r.startswith("./"):
        r = r[2:]
    r = r.strip("/")
    return r


def load_allowed_roots() -> List[str]:
    raw = os.environ.get("MCP04_ROOTS", "").strip()
    if not raw:
        roots = ["projects/mcp"]
    else:
        roots = [normalize_root(x) for x in raw.split(",") if normalize_root(x)]
        if not roots:
            roots = ["projects/mcp"]
    # de-dup preserve order
    seen = set()
    out = []
    for r in roots:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def roots_hash(roots: List[str]) -> str:
    payload = json.dumps(roots, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def is_allowed_rel(rel: str, allowed_roots: List[str]) -> bool:
    rel = (rel or "").replace("\\", "/").lstrip("/")
    for root in allowed_roots:
        if rel == root or rel.startswith(root + "/"):
            return True
    return False


def safe_resolve_under(repo_root: Path, rel_path: str) -> Path:
    if rel_path.startswith("/") or rel_path.startswith("\\"):
        raise ValueError("absolute paths are not allowed")

    rel_path = rel_path.replace("\\", "/")
    if rel_path == ".." or rel_path.startswith("../") or "/../" in rel_path:
        raise ValueError("path traversal is not allowed")

    target = (repo_root / rel_path).resolve()
    try:
        target.relative_to(repo_root)
    except Exception:
        raise ValueError("path escapes repo root")
    return target


def json_text(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def log_enabled() -> bool:
    return os.environ.get("MCP05_LOG_ENABLED", "1").strip() not in ("0", "false", "False", "no", "NO")


def log_path(repo_root: Path) -> Path:
    p = os.environ.get("MCP05_LOG_PATH", "runtime_data/mcp05_policy_decisions.jsonl").strip()
    # allow relative to repo root
    path = (repo_root / p).resolve() if not os.path.isabs(p) else Path(p).resolve()
    return path


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


@dataclass
class Decision:
    ok: bool
    code: str
    message: str
    rel: str
    decoded: str


def make_decision(
    *,
    request_id: str,
    uri: str,
    resource_kind: str,
    raw_path_param: str,
    decoded_rel: str,
    decision: Decision,
    allowed_roots: List[str],
    roots_hash_value: str,
) -> dict:
    return {
        "schema": DECISION_SCHEMA,
        "ts": utc_iso(),
        "request_id": request_id,
        "uri": uri,
        "resource_kind": resource_kind,      # "file" | "dir"
        "path_param_raw": raw_path_param,    # encoded segment
        "path_decoded": decoded_rel,         # decoded relative path
        "decision": "ALLOW" if decision.ok else "DENY",
        "reason": {"code": decision.code, "message": decision.message},
        "policy": {"allowed_roots": allowed_roots, "roots_hash": roots_hash_value},
    }


def build_server():
    from mcp.server.fastmcp import FastMCP

    ROOT = repo_root_from_here()
    ALLOWED = load_allowed_roots()
    ROOTS_HASH = roots_hash(ALLOWED)
    LOG_PATH = log_path(ROOT)

    mcp = FastMCP(name="MCP-05 PolicyLog", json_response=True)

    @mcp.resource(
        "mcpfs://repo/policy",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="Current resource policy + encoding contract.",
    )
    def policy() -> dict:
        return {
            "schema": POLICY_SCHEMA,
            "generated_at": utc_iso(),
            "repo_root": str(ROOT),
            "allowed_roots": ALLOWED,
            "roots_hash": ROOTS_HASH,
            "encoded_path_contract": {
                "template": "{path}",
                "encoding": "URL-encode full relative path into ONE segment (encode '/' as %2F).",
                "example_rel": "projects/mcp/05-policy-log/main.py",
                "example_encoded": quote("projects/mcp/05-policy-log/main.py", safe=""),
            },
            "logging": {
                "enabled": log_enabled(),
                "path": str(LOG_PATH),
                "schema": DECISION_SCHEMA,
                "note": "Each resource access decision (ALLOW/DENY) appends one JSONL line.",
            },
        }

    @mcp.resource(
        "mcpfs://repo/index",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="Index limited to allowed roots (policy-filtered).",
    )
    def repo_index() -> dict:
        entries = []
        for r in ALLOWED:
            entries.append({"name": r, "type": "dir", "uri": f"mcpfs://repo/dir/{quote(r, safe='')}"})
        return {"schema": INDEX_SCHEMA, "generated_at": utc_iso(), "entries": entries}

    def policy_check(rel: str) -> Decision:
        rel = (rel or "").replace("\\", "/").lstrip("/")
        if not rel:
            return Decision(False, "FORBIDDEN", "empty path is not allowed", rel, rel)
        if not is_allowed_rel(rel, ALLOWED):
            return Decision(False, "FORBIDDEN", "path is outside allowed_roots", rel, rel)
        try:
            safe_resolve_under(ROOT, rel)
        except Exception as e:
            return Decision(False, "BAD_PATH", str(e), rel, rel)
        return Decision(True, "OK", "allowed", rel, rel)

    def maybe_log(obj: dict) -> None:
        if not log_enabled():
            return
        try:
            append_jsonl(LOG_PATH, obj)
        except Exception as e:
            # Never break protocol due to logging failures; log to stderr only.
            print(f"[MCP-05] log write failed: {e}", file=sys.stderr)

    @mcp.resource(
        "mcpfs://repo/dir/{path}",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": False},
        description="List a directory under allowed roots. {path} must be URL-encoded. (Logs decision)",
    )
    def list_dir(path: str) -> dict:
        req_id = f"req_{uuid.uuid4().hex}"
        raw = path or ""
        decoded = unquote(raw)
        rel = decoded.replace("\\", "/").lstrip("/")

        d = policy_check(rel)
        maybe_log(
            make_decision(
                request_id=req_id,
                uri=f"mcpfs://repo/dir/{raw}",
                resource_kind="dir",
                raw_path_param=raw,
                decoded_rel=rel,
                decision=d,
                allowed_roots=ALLOWED,
                roots_hash_value=ROOTS_HASH,
            )
        )

        if not d.ok:
            return {
                "schema": DIR_SCHEMA,
                "ok": False,
                "error": {"code": d.code, "message": d.message, "path": rel},
                "generated_at": utc_iso(),
                "request_id": req_id,
            }

        target = safe_resolve_under(ROOT, rel)
        if not target.exists():
            return {
                "schema": DIR_SCHEMA,
                "ok": False,
                "error": {"code": "NOT_FOUND", "message": "directory not found", "path": rel},
                "generated_at": utc_iso(),
                "request_id": req_id,
            }
        if not target.is_dir():
            return {
                "schema": DIR_SCHEMA,
                "ok": False,
                "error": {"code": "NOT_A_DIR", "message": "path is not a directory", "path": rel},
                "generated_at": utc_iso(),
                "request_id": req_id,
            }

        children: List[dict] = []
        for p in sorted(target.iterdir()):
            if p.name in (".git", ".venv", "__pycache__"):
                continue
            rel_child = str(p.relative_to(ROOT)).replace("\\", "/")
            if not is_allowed_rel(rel_child, ALLOWED):
                continue
            enc = quote(rel_child, safe="")
            children.append(
                {"name": p.name, "type": "dir" if p.is_dir() else "file",
                 "uri": f"mcpfs://repo/dir/{enc}" if p.is_dir() else f"mcpfs://repo/file/{enc}"}
            )
            if len(children) >= 200:
                break

        return {
            "schema": DIR_SCHEMA,
            "ok": True,
            "path": rel,
            "generated_at": utc_iso(),
            "request_id": req_id,
            "children": children,
        }

    @mcp.resource(
        "mcpfs://repo/file/{path}",
        mime_type="text/plain",
        annotations={"readOnlyHint": True, "idempotentHint": False},
        description="Read a text file under allowed roots. {path} must be URL-encoded. (Logs decision)",
    )
    def read_file(path: str) -> str:
        req_id = f"req_{uuid.uuid4().hex}"
        raw = path or ""
        decoded = unquote(raw)
        rel = decoded.replace("\\", "/").lstrip("/")

        d = policy_check(rel)
        maybe_log(
            make_decision(
                request_id=req_id,
                uri=f"mcpfs://repo/file/{raw}",
                resource_kind="file",
                raw_path_param=raw,
                decoded_rel=rel,
                decision=d,
                allowed_roots=ALLOWED,
                roots_hash_value=ROOTS_HASH,
            )
        )

        if not d.ok:
            return json_text(
                {"ok": False, "error": {"code": d.code, "message": d.message, "path": rel},
                 "generated_at": utc_iso(), "request_id": req_id}
            )

        target = safe_resolve_under(ROOT, rel)
        if not target.exists() or not target.is_file():
            return json_text(
                {"ok": False, "error": {"code": "NOT_FOUND", "message": "file not found", "path": rel},
                 "generated_at": utc_iso(), "request_id": req_id}
            )

        size = target.stat().st_size
        if size > 512_000:
            return json_text(
                {"ok": False, "error": {"code": "TOO_LARGE", "message": "file exceeds size cap", "bytes": size, "path": rel},
                 "generated_at": utc_iso(), "request_id": req_id}
            )

        return target.read_text(encoding="utf-8", errors="replace")

    return mcp


async def run_client(script_path: str) -> int:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[script_path, "server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            pol = await session.read_resource("mcpfs://repo/policy")
            print("policy ->", (pol.contents[0].text or "")[:120].replace("\n", " "))

            # allowed
            rel_ok = "projects/mcp/05-policy-log/main.py"
            ok_uri = f"mcpfs://repo/file/{quote(rel_ok, safe='')}"
            okc = await session.read_resource(ok_uri)
            print("read allowed chars ->", len(okc.contents[0].text or ""))

            # forbidden
            rel_bad = ".gitignore"
            bad_uri = f"mcpfs://repo/file/{quote(rel_bad, safe='')}"
            badc = await session.read_resource(bad_uri)
            print("read forbidden ->", (badc.contents[0].text or "")[:120].replace("\n", " "))

            return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["server", "client"])
    args = parser.parse_args()

    if args.mode == "server":
        server = build_server()
        server.run(transport="stdio")
        return 0

    script_path = os.path.abspath(__file__)
    return asyncio.run(run_client(script_path))


if __name__ == "__main__":
    raise SystemExit(main())
