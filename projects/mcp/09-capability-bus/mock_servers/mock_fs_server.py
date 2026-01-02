#!/usr/bin/env python3
# projects/mcp/09-capability-bus/mock_servers/mock_fs_server.py

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any, Dict

JSON = Dict[str, Any]


def ok(req_id: Any, result: Any) -> JSON:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def err(req_id: Any, code: int, message: str, data: Any = None) -> JSON:
    e: JSON = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": e}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        rid = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        if method == "tools/list":
            resp = ok(rid, {
                "tools": [
                    {"name": "read_file", "description": "Read a local file (mock)."}
                ]
            })

        elif method == "tools/call":
            name = params.get("name")
            args = params.get("args") or {}

            if name == "read_file":
                p = args.get("path")
                if p == "__error__":
                    resp = err(rid, 1234, "mock_fs_server forced error", {"hint": "pass a real path"})
                else:
                    try:
                        text = Path(p).read_text(encoding="utf-8")
                        resp = ok(rid, {"content": text})
                    except Exception as e:
                        resp = err(rid, 1001, "read_file failed", {"path": p, "error": str(e)})
            else:
                resp = err(rid, -32602, f"Unknown tool: {name}")

        elif method == "resources/list":
            resp = ok(rid, {
                "resources": [
                    {"uri": "file://README.md", "description": "Mock readme resource"}
                ]
            })

        elif method == "resources/read":
            uri = params.get("uri")
            if uri == "file://README.md":
                resp = ok(rid, {"text": "hello from mock fs resource"})
            else:
                resp = err(rid, 2001, "resource not found", {"uri": uri})

        else:
            resp = err(rid, -32601, f"Method not found: {method}")

        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
