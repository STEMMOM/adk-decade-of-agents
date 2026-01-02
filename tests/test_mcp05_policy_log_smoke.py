import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote


async def _smoke():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "projects" / "mcp" / "05-policy-log" / "main.py"
    assert script.exists(), f"missing: {script}"

    with tempfile.TemporaryDirectory() as td:
        log_file = Path(td) / "mcp05_policy_decisions.jsonl"

        env = os.environ.copy()
        env["MCP05_LOG_PATH"] = str(log_file)
        env["MCP05_LOG_ENABLED"] = "1"
        # default MCP04_ROOTS is projects/mcp

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(script), "server"],
            env=env,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # allowed read
                rel_ok = "projects/mcp/05-policy-log/main.py"
                ok_uri = f"mcpfs://repo/file/{quote(rel_ok, safe='')}"
                okc = await session.read_resource(ok_uri)
                assert "MCP-05" in (okc.contents[0].text or "")

                # forbidden read
                rel_bad = ".gitignore"
                bad_uri = f"mcpfs://repo/file/{quote(rel_bad, safe='')}"
                badc = await session.read_resource(bad_uri)
                obj = json.loads(badc.contents[0].text or "{}")
                assert obj["ok"] is False
                assert obj["error"]["code"] == "FORBIDDEN"

        # Verify JSONL log written
        assert log_file.exists()
        lines = [ln for ln in log_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) >= 2

        records = [json.loads(ln) for ln in lines[-2:]]
        decisions = {r.get("decision") for r in records}
        assert "ALLOW" in decisions
        assert "DENY" in decisions
        for r in records:
            assert r.get("schema") == "mcp-policy-decision/v1"
            assert "policy" in r and "roots_hash" in r["policy"]


def test_mcp05_policy_log_smoke():
    asyncio.run(_smoke())
