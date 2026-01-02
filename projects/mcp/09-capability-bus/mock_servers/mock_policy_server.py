#!/usr/bin/env python3
# projects/mcp/09-capability-bus/mock_servers/mock_policy_server.py

from __future__ import annotations
import json
import sys
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
            resp = ok(rid, {"tools": [{"name": "evaluate", "description": "Mock policy evaluate"}]})

        elif method == "tools/call":
            name = params.get("name")
            args = params.get("args") or {}

            if name == "evaluate":
                # silly mock: deny if action contains "docs"
                action = (args.get("action") or "").lower()
                decision = "DENY" if "docs" in action else "ALLOW"
                resp = ok(rid, {"decision": decision, "policy_version": "mock-v0"})
            else:
                resp = err(rid, -32602, f"Unknown tool: {name}")

        elif method == "resources/list":
            resp = ok(rid, {"resources": []})

        elif method == "resources/read":
            resp = err(rid, 2002, "no resources in mock_policy_server")

        else:
            resp = err(rid, -32601, f"Method not found: {method}")

        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
