#!/usr/bin/env python3
"""
MCP-04 — Roots + Policy Gate for Resources (repo-root, read-only)

Run:
  python projects/mcp/04-roots-policy/main.py server
  python projects/mcp/04-roots-policy/main.py client

Config:
  MCP04_ROOTS="projects/mcp,docs"   (comma-separated, repo-relative)
Default:
  projects/mcp
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote, unquote

POLICY_SCHEMA = "mcpfs-roots-policy/v1"
INDEX_SCHEMA = "mcpfs-index/v1"
DIR_SCHEMA = "mcpfs-dir/v1"


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root_from_here() -> Path:
    # .../projects/mcp/04-roots-policy/main.py -> repo root is parents[3]
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
    # de-dup while preserving order
    seen = set()
    out = []
    for r in roots:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def is_allowed_rel(rel: str, allowed_roots: List[str]) -> bool:
    rel = (rel or "").replace("\\", "/").lstrip("/")
    # Must be under at least one allowed root
    for root in allowed_roots:
        if rel == root or rel.startswith(root + "/"):
            return True
    return False


def safe_resolve_under(repo_root: Path, rel_path: str) -> Path:
    """
    Resolve rel_path under repo_root and ensure it doesn't escape repo_root.
    """
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


def build_server():
    from mcp.server.fastmcp import FastMCP

    ROOT = repo_root_from_here()
    ALLOWED = load_allowed_roots()

    mcp = FastMCP(name="MCP-04 RootsPolicy", json_response=True)

    @mcp.resource(
        "mcpfs://repo/policy",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="Resource access policy: allowed roots + encoded-path contract.",
    )
    def policy() -> dict:
        return {
            "schema": POLICY_SCHEMA,
            "generated_at": utc_iso(),
            "repo_root": str(ROOT),
            "allowed_roots": ALLOWED,
            "contract": {
                "path_param": "{path}",
                "encoding": "URL-encode full relative path into ONE segment (encode '/' as %2F).",
                "examples": [
                    {
                        "rel": "projects/mcp/04-roots-policy/main.py",
                        "encoded": quote("projects/mcp/04-roots-policy/main.py", safe=""),
                        "uri": "mcpfs://repo/file/<encoded>",
                    }
                ],
            },
        }

    @mcp.resource(
        "mcpfs://repo/index",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="Index limited to allowed roots (policy-governed).",
    )
    def repo_index() -> dict:
        entries = []
        for r in ALLOWED:
            entries.append(
                {
                    "name": r,
                    "type": "dir",
                    "uri": f"mcpfs://repo/dir/{quote(r, safe='')}",
                }
            )
        return {
            "schema": INDEX_SCHEMA,
            "generated_at": utc_iso(),
            "entries": entries,
            "note": "Index is policy-filtered to allowed_roots only.",
        }

    @mcp.resource(
        "mcpfs://repo/dir/{path}",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="List a directory under allowed roots. {path} must be URL-encoded.",
    )
    def list_dir(path: str) -> dict:
        # decode the single-segment encoded path into real multi-segment path
        path = unquote(path or "")
        rel = path.replace("\\", "/").lstrip("/")

        if not rel:
            return {
                "schema": DIR_SCHEMA,
                "ok": False,
                "error": {"code": "FORBIDDEN", "message": "root listing is not allowed; use mcpfs://repo/index", "path": rel},
                "generated_at": utc_iso(),
            }

        if not is_allowed_rel(rel, ALLOWED):
            return {
                "schema": DIR_SCHEMA,
                "ok": False,
                "error": {"code": "FORBIDDEN", "message": "path is outside allowed_roots", "path": rel},
                "generated_at": utc_iso(),
            }

        try:
            target = safe_resolve_under(ROOT, rel)
        except Exception as e:
            return {
                "schema": DIR_SCHEMA,
                "ok": False,
                "error": {"code": "BAD_PATH", "message": str(e), "path": rel},
                "generated_at": utc_iso(),
            }

        if not target.exists():
            return {
                "schema": DIR_SCHEMA,
                "ok": False,
                "error": {"code": "NOT_FOUND", "message": "directory not found", "path": rel},
                "generated_at": utc_iso(),
            }
        if not target.is_dir():
            return {
                "schema": DIR_SCHEMA,
                "ok": False,
                "error": {"code": "NOT_A_DIR", "message": "path is not a directory", "path": rel},
                "generated_at": utc_iso(),
            }

        children: List[dict] = []
        for p in sorted(target.iterdir()):
            if p.name in (".git", ".venv", "__pycache__"):
                continue
            rel_child = str(p.relative_to(ROOT)).replace("\\", "/")

            # extra guard: never return children outside allowed roots
            if not is_allowed_rel(rel_child, ALLOWED):
                continue

            enc = quote(rel_child, safe="")
            children.append(
                {
                    "name": p.name,
                    "type": "dir" if p.is_dir() else "file",
                    "uri": f"mcpfs://repo/dir/{enc}" if p.is_dir() else f"mcpfs://repo/file/{enc}",
                }
            )
            if len(children) >= 200:
                break

        return {
            "schema": DIR_SCHEMA,
            "ok": True,
            "path": rel,
            "generated_at": utc_iso(),
            "children": children,
        }

    @mcp.resource(
        "mcpfs://repo/file/{path}",
        mime_type="text/plain",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="Read a text file under allowed roots. {path} must be URL-encoded.",
    )
    def read_file(path: str) -> str:
        path = unquote(path or "")
        rel = path.replace("\\", "/").lstrip("/")

        if not rel or not is_allowed_rel(rel, ALLOWED):
            return json_text(
                {
                    "ok": False,
                    "error": {"code": "FORBIDDEN", "message": "path is outside allowed_roots", "path": rel},
                    "generated_at": utc_iso(),
                }
            )

        try:
            target = safe_resolve_under(ROOT, rel)
        except Exception as e:
            return json_text(
                {
                    "ok": False,
                    "error": {"code": "BAD_PATH", "message": str(e), "path": rel},
                    "generated_at": utc_iso(),
                }
            )

        if not target.exists() or not target.is_file():
            return json_text(
                {
                    "ok": False,
                    "error": {"code": "NOT_FOUND", "message": "file not found", "path": rel},
                    "generated_at": utc_iso(),
                }
            )

        size = target.stat().st_size
        if size > 512_000:
            return json_text(
                {
                    "ok": False,
                    "error": {"code": "TOO_LARGE", "message": "file exceeds size cap", "bytes": size, "path": rel},
                    "generated_at": utc_iso(),
                }
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

            # 1) read policy
            p = await session.read_resource("mcpfs://repo/policy")
            print("policy mime ->", p.contents[0].mimeType)

            # 2) list templates
            t = await session.list_resource_templates()
            print("templates ->", [x.uriTemplate for x in t.resourceTemplates])

            # 3) read an allowed file (this file)
            rel_ok = "projects/mcp/04-roots-policy/main.py"
            enc_ok = quote(rel_ok, safe="")
            okc = await session.read_resource(f"mcpfs://repo/file/{enc_ok}")
            print("read allowed chars ->", len(okc.contents[0].text or ""))

            # 4) try forbidden file (repo root .gitignore or README.md)
            rel_bad = ".gitignore"
            enc_bad = quote(rel_bad, safe="")
            badc = await session.read_resource(f"mcpfs://repo/file/{enc_bad}")
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
