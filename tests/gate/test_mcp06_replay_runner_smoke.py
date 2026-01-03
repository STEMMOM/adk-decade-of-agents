import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from tests.gate._repo_root import repo_root

pytestmark = pytest.mark.gate


def test_mcp06_replay_runner_smoke():
    root = repo_root()
    runner = root / "projects" / "mcp" / "06-replay-runner" / "main.py"
    assert runner.exists()

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        plan = td / "plan.json"
        report = td / "report.json"

        # 1) init plan
        subprocess.check_call([sys.executable, str(runner), "init-plan", "--out", str(plan)], cwd=str(root))

        # 2) run replay (default server is MCP-05)
        subprocess.check_call([sys.executable, str(runner), "run", "--plan", str(plan), "--out", str(report)], cwd=str(root))

        obj = json.loads(report.read_text(encoding="utf-8"))
        assert obj["schema"] == "mcp-replay-report/v1"
        assert obj["stats"]["total"] == 2

        steps = obj["steps"]
        decisions = [s["decision"] for s in steps]
        assert "ALLOW" in decisions
        assert "DENY" in decisions

        # The DENY step should have FORBIDDEN by default starter plan
        deny = [s for s in steps if s["decision"] == "DENY"][0]
        assert deny["error_code"] == "FORBIDDEN"
