.PHONY: help protocol-check protocol-test clean institution-check

# ---------- Meta ----------

help:
	@echo ""
	@echo "Institutional Makefile v1"
	@echo ""
	@echo "Mandatory gates:"
	@echo "  make protocol-check     Verify protocol schemas & invariants (highest law)"
	@echo "  make institution-check  Alias for all mandatory institutional checks"
	@echo ""
	@echo "Utility:"
	@echo "  make clean              Remove Python cache files"
	@echo ""

# ---------- Protocols (Highest Law) ----------

protocol-check:
	@echo "==> Verifying protocol law (schemas + invariants)"
	pytest -q \
	  tests/protocols/test_event_envelope_v1_schema.py \
	  tests/protocols/test_event_envelope_v1_invariants.py \
	  tests/protocols/test_system_process_v1_schema.py \
	  tests/protocols/test_system_process_v1_invariants.py

protocol-test: protocol-check

# ---------- Institutional Gate ----------

institution-check: protocol-check
	@echo "==> Institutional checks passed"

institution-check-all:
	$(MAKE) protocol-check
	rm -f runtime_data/events.jsonl && python -m projects.p00-agent-os-mvp.src.main
	python scripts/verify_events_ledger.py --in runtime_data/events.jsonl --fail-on-nonv1

# ---------- Hygiene ----------

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete || true
