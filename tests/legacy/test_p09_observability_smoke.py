# tests/test_p09_observability_smoke.py
from __future__ import annotations

import json
import tempfile
import os
from pathlib import Path
import pytest

from scripts.observability.obs_export_p09 import export as export_p09
from scripts.observability.obs_aggregate_daily import main as agg_main  # if your aggregator has a main()
# If your aggregator doesn't expose main cleanly, see note below.

LEDGER_SAMPLE = """\
{"event_type":"tool.call","run_id":"run_test_001","session_id":"p00-demo-session","timestamp":"2025-12-22T01:44:28.682947Z","layer":"tool","payload":{"tool_name":"fake_search","args":{"q":"AI news this week"}}}
{"event_type":"tool.result","run_id":"run_test_001","session_id":"p00-demo-session","timestamp":"2025-12-22T01:44:28.683038Z","layer":"tool","payload":{"tool_name":"fake_search","result":{"ok":true}}}
"""

pytestmark = pytest.mark.legacy

def test_p09_observability_smoke():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        os.chdir(tmp)
        runtime_data = tmp / "runtime_data"
        runtime_data.mkdir(parents=True, exist_ok=True)
        events_file = runtime_data / "events.jsonl"
        # system boot/shutdown with authoritative run_id
        events_file.write_text(
            """{"event_type":"system.boot","ts":"2025-12-22T01:44:28.600000Z","payload":{"run_id":"run_test_001"}}
{"event_type":"system.shutdown","ts":"2025-12-22T01:44:29.600000Z","payload":{"run_id":"run_test_001"}}
""",
            encoding="utf-8",
        )

        ledger_in = tmp / "observability_events.jsonl"
        p09_out = tmp / "observability_events_p09.jsonl"
        summary_out = tmp / "daily_metrics_summary_2025-12-22.json"

        ledger_in.write_text(LEDGER_SAMPLE, encoding="utf-8")

        # 1) export to P09 canonical
        export_p09(ledger_in, p09_out)
        assert p09_out.exists()
        assert p09_out.stat().st_size > 0
        # validate run_id/session_id semantics
        records = [json.loads(line) for line in p09_out.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(rec["event_type"] == "run_started" for rec in records)
        for rec in records:
            assert rec.get("run_id", "").startswith("run_")
            if rec["event_type"].startswith("tool_call"):
                assert rec.get("session_id")

        # 2) aggregate daily summary
        # Preferred: call aggregator logic as a function. If not available, run it via subprocess.
        import subprocess
        subprocess.check_call([
            "python",
            "-m",
            "scripts.observability.obs_aggregate_daily",
            "--events",
            str(p09_out),
            "--day",
            "2025-12-22",
            "--out",
            str(summary_out),
        ])

        assert summary_out.exists()

        # 3) assertions
        data = json.loads(summary_out.read_text(encoding="utf-8"))
        assert data["day"] == "2025-12-22"
        assert data["run_summary"]["runs_total"] == 1
        assert data["run_summary"]["runs_by_status"].get("success", 0) == 1
        assert data["tooling"]["tool_calls_total"] == 1
        assert data["tooling"]["tool_calls_by_name"]["fake_search"]["success"] == 1
