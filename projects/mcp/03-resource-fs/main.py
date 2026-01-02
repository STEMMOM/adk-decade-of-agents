#!/usr/bin/env python3
"""
MCP-03 — Resource FS (repo-root, read-only)

Run:
  python projects/mcp/03-resource-fs/main.py server
  python projects/mcp/03-resource-fs/main.py client
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote, unquote

MCPFS_INDEX_SCHEMA = "mcpfs-index/v1"
MCPFS_DIR_SCHEMA = "mcpfs-dir/v1"


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root_from_here() -> Path:
    # .../projects/mcp/03-resource-fs/main.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def safe_resolve_under(root: Path, rel_path: str) -> Path:
    """
    Resolve rel_path under root and ensure it doesn't escape root.
    """
    # Disallow absolute paths
    if rel_path.startswith("/") or rel_path.startswith("\\"):
        raise ValueError("absolute paths are not allowed")

    # Normalize path separators from URIs
    rel_path = rel_path.replace("\\", "/")

    # Basic traversal guard (still verify with resolve+relative_to)
    if rel_path.startswith("../") or "/../" in rel_path or rel_path == "..":
        raise ValueError("path traversal is not allowed")

    target = (root / rel_path).resolve()
    try:
        target.relative_to(root)
    except Exception:
        raise ValueError("path escapes repo root")
    return target


def sniff_mime(path: Path) -> str:
    # Minimal heuristic; good enough for now.
    ext = path.suffix.lower()
    if ext in (".md", ".txt", ".log"):
        return "text/plain"
    if ext in (".py", ".json", ".yaml", ".yml", ".toml", ".sh"):
        return "text/plain"
    return "application/octet-stream"


def build_server():
    from mcp.server.fastmcp import FastMCP

    ROOT = repo_root_from_here()

    mcp = FastMCP(name="MCP-03 ResourceFS", json_response=True)

    @mcp.resource(
        "mcpfs://repo/index",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="Quick index of repo root (top-level entries, limited).",
    )
    def repo_index() -> dict:
        entries: List[dict] = []
        for p in sorted(ROOT.iterdir()):
            # skip venv + git internals
            if p.name in (".git", ".venv", "__pycache__"):
                continue
            entries.append(
                {
                    "name": p.name,
                    "type": "dir" if p.is_dir() else "file",
                }
            )
            if len(entries) >= 50:
                break

        return {
            "schema": MCPFS_INDEX_SCHEMA,
            "root": str(ROOT),
            "generated_at": utc_iso(),
            "entries": entries,
            "note": "Use mcpfs://repo/file/{path} to read files and mcpfs://repo/dir/{path} to list directories.",
        }

    @mcp.resource(
        "mcpfs://repo/dir/{path}",
        mime_type="application/json",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="List a directory under the repo root. Returns JSON.",
    )
    def list_dir(path: str) -> dict:
        path = unquote(path)
        target = safe_resolve_under(ROOT, path)
        if not target.exists():
            return {
                "schema": MCPFS_DIR_SCHEMA,
                "ok": False,
                "error": {"code": "NOT_FOUND", "message": "directory not found", "path": path},
                "generated_at": utc_iso(),
            }
        if not target.is_dir():
            return {
                "schema": MCPFS_DIR_SCHEMA,
                "ok": False,
                "error": {"code": "NOT_A_DIR", "message": "path is not a directory", "path": path},
                "generated_at": utc_iso(),
            }

        children: List[dict] = []
        for p in sorted(target.iterdir()):
            if p.name in (".git", ".venv", "__pycache__"):
                continue
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            children.append(
                {
                    "name": p.name,
                    "type": "dir" if p.is_dir() else "file",
                    "uri": f"mcpfs://repo/dir/{quote(rel, safe='')}" if p.is_dir() else f"mcpfs://repo/file/{quote(rel, safe='')}",
                }
            )
            if len(children) >= 200:
                break

        return {
            "schema": MCPFS_DIR_SCHEMA,
            "ok": True,
            "path": path,
            "generated_at": utc_iso(),
            "children": children,
        }

    @mcp.resource(
        "mcpfs://repo/file/{path}",
        mime_type="text/plain",
        annotations={"readOnlyHint": True, "idempotentHint": True},
        description="Read a text file under the repo root. Returns text.",
    )
    def read_file(path: str) -> str:
        path = unquote(path)
        target = safe_resolve_under(ROOT, path)
        if not target.exists() or not target.is_file():
            return json.dumps(
                {
                    "ok": False,
                    "error": {"code": "NOT_FOUND", "message": "file not found", "path": path},
                    "generated_at": utc_iso(),
                },
                ensure_ascii=False,
                indent=2,
            )

        # guard huge files
        size = target.stat().st_size
        if size > 512_000:  # 512KB cap for now
            return json.dumps(
                {
                    "ok": False,
                    "error": {"code": "TOO_LARGE", "message": "file exceeds size cap", "bytes": size, "path": path},
                    "generated_at": utc_iso(),
                },
                ensure_ascii=False,
                indent=2,
            )

        # read as utf-8 with replacement to avoid crashing on odd bytes
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

            # 1) list resources
            rlist = await session.list_resources()
            print("resources/list ->", [r.uri for r in rlist.resources][:10])

            # 2) list templates
            tlist = await session.list_resource_templates()
            print("resources/templates/list ->", [t.uriTemplate for t in tlist.resourceTemplates])

            # 3) read index
            idx = await session.read_resource("mcpfs://repo/index")
            print("read index mime ->", idx.contents[0].mimeType)

            # 4) read a known file (this file itself)
            rel = "projects/mcp/03-resource-fs/main.py"
            enc = quote(rel, safe="")
            content = await session.read_resource(f"mcpfs://repo/file/{enc}")
            text = content.contents[0].text
            print("read file chars ->", len(text))

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
