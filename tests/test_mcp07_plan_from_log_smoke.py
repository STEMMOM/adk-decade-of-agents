import json
import subprocess
import sys
from pathlib import Path


def test_mcp07_plan_from_log_smoke(tmp_path: Path):
    log = tmp_path / "mcp05_policy_decisions.jsonl"
    out = tmp_path / "mcp07_plan.json"

    log.write_text(
        '{"request":{"uri":"a"},"decision":"ALLOW"}\n'
        '{"request":{"uri":"b"},"decision":"DENY","error_code":"X"}\n'
        '{"request":{"uri":"a"},"decision":"DENY","error_code":"Y"}\n'
    )

    subprocess.check_call([
        sys.executable,
        "-m", "projects.mcp.07-plan-from-log.main",
        "build-plan",
        "--in", str(log),
        "--out", str(out),
    ])

    plan = json.loads(out.read_text())
    assert len(plan["steps"]) == 2
