# adk_runtime/memory_gate_p08.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .event_ledger import EventLedger
from .memory_schema import MemoryZone
from .paths import RUNTIME_DATA_DIR, ensure_runtime_dirs


@dataclass(frozen=True)
class RuntimeSchema:
    supported_schema_version: int = 0
    supported_store_version: int = 0


class P08MemoryGate:
    """
    Wraps the legacy P07 memory store with P08 startup confrontation + validation.
    Refusal over silent compatibility.
    """

    def __init__(self, legacy_store, ledger: EventLedger, runtime_schema: RuntimeSchema | None = None):
        self.legacy_store = legacy_store
        self.ledger = ledger
        self.runtime = runtime_schema or RuntimeSchema()
        self._write_block_reason: Optional[str] = None

    def startup_confrontation(self, *, session_id: Optional[str] = None) -> None:
        ensure_runtime_dirs()
        store = self.legacy_store.load_memory()

        store_version_raw = store.get("store_version")
        current_schema_raw = store.get("schema_version") or store.get("current_schema_version")

        store_version = self._to_int(store_version_raw)
        current_schema = self._to_int(current_schema_raw)

        ok_store = (store_version is None) or (store_version == self.runtime.supported_store_version)
        self.ledger.append(
            "memory.version_check",
            {"ok": ok_store, "store_version": store_version, "supported": self.runtime.supported_store_version},
            session_id=session_id,
        )
        if not ok_store:
            self._quarantine(store, reason="store_version_mismatch", session_id=session_id, block_writes=True)
            return

        if current_schema is None:
            self._quarantine(store, reason="missing_or_invalid_schema_version", session_id=session_id, block_writes=False)
            return

        if current_schema > self.runtime.supported_schema_version:
            # future schema: refuse writes
            self._quarantine(store, reason="future_schema_version", session_id=session_id, block_writes=True)
            return

        if current_schema < self.runtime.supported_schema_version:
            # older schema: quarantine and reset active zones
            self._quarantine(store, reason="older_schema_version", session_id=session_id, block_writes=False)
            return

    def load_memory(self) -> Dict[str, Any]:
        return self.legacy_store.load_memory()

    def save_memory(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Mirrors legacy P07 save_memory signature, adds P08 validation.
        """
        session_id: Optional[str] = kwargs.get("session_id")

        if self._write_block_reason:
            decision = {
                "decision": "blocked",
                "reason": self._write_block_reason,
                "rule_hits": [{"rule_id": "P08-QUARANTINED", "severity": "hard"}],
            }
            self._emit_block(decision, session_id=session_id)
            return {"status": "blocked", "decision": decision}

        schema_version = kwargs.get("schema_version")
        zone = kwargs.get("zone")
        provenance = kwargs.get("provenance")
        promotion_from = kwargs.get("promotion_from")
        promotion_authorized = kwargs.get("promotion_authorized")

        validation_error = self._validate_entry(schema_version, zone, provenance, promotion_from, promotion_authorized)
        if validation_error:
            self._emit_block(
                {
                    "decision": "blocked",
                    "reason": validation_error,
                    "rule_hits": [{"rule_id": "P08-VALIDATION", "severity": "hard"}],
                },
                session_id=session_id,
            )
            return {"status": "blocked", "decision": {"reason": validation_error}}

        self.ledger.append(
            "memory.zone_validation",
            {"ok": True, "zone": zone, "schema_version": schema_version},
            session_id=session_id,
        )

        return self.legacy_store.save_memory(data, **kwargs)

    # -------------------------
    # Internal helpers
    # -------------------------

    def _quarantine(self, store: Dict[str, Any], *, reason: str, session_id: Optional[str], block_writes: bool) -> None:
        """
        Do not silently proceed. Record legacy snapshot and refuse writes.
        """
        if block_writes:
            self._write_block_reason = reason
        else:
            self._write_block_reason = None
        legacy_snapshot = {"reason": reason, "store": store}
        # Persist quarantine marker alongside legacy snapshot.
        self.legacy_store._apply_patch("legacy_quarantine", legacy_snapshot)  # type: ignore[attr-defined]

        # Align store schema to runtime for new writes when not blocking writes.
        if not block_writes:
            store["current_schema_version"] = self.runtime.supported_schema_version
            self.legacy_store._apply_patch("current_schema_version", self.runtime.supported_schema_version)  # type: ignore[attr-defined]

        self.ledger.append(
            "memory.legacy_detected",
            {"reason": reason, "action": "quarantine_and_refuse_writes"},
            session_id=session_id,
        )

    def _validate_entry(
        self,
        schema_version: Any,
        zone: Any,
        provenance: Any,
        promotion_from: Any,
        promotion_authorized: Any,
    ) -> Optional[str]:
        if schema_version is None:
            return "UC-01: missing schema_version"
        if not isinstance(schema_version, int):
            return "schema_version must be int"
        if schema_version > self.runtime.supported_schema_version:
            return "UC-05: unsupported future schema_version"
        if schema_version < self.runtime.supported_schema_version:
            return "write must use current schema_version; older versions belong in legacy via migration"

        if zone is None:
            return "UC-02: missing zone"
        try:
            zone_enum = MemoryZone(zone)
        except Exception:
            return f"invalid zone: {zone}"
        if zone_enum == MemoryZone.LEGACY:
            return "UC-03: cannot write to legacy zone"

        if zone_enum == MemoryZone.WORLD_STATE:
            if not self._provenance_ok(provenance):
                return "UC-07: world_state requires minimal provenance"

        if promotion_from is not None and promotion_authorized is not True:
            return "UC-06: promotion to world_state requires explicit authorization"

        return None

    def _provenance_ok(self, prov: Optional[Dict[str, Any]]) -> bool:
        if not prov or not isinstance(prov, dict):
            return False
        source_type = prov.get("source_type")
        allowed = {"user_declared", "tool_verified", "human_approved"}
        return source_type in allowed

    def _emit_block(self, decision: Dict[str, Any], *, session_id: Optional[str]) -> None:
        self.ledger.append(
            "memory.zone_validation",
            {"ok": False, "decision": decision},
            session_id=session_id,
        )

    def _to_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                try:
                    fval = float(value)
                    if fval.is_integer():
                        return int(fval)
                except ValueError:
                    return None
                return None
        return None


def make_p08_gate(legacy_store_module) -> P08MemoryGate:
    ensure_runtime_dirs()
    ledger_path = RUNTIME_DATA_DIR / "memory_gate_ledger.jsonl"
    ledger = EventLedger(ledger_path)
    runtime = RuntimeSchema()
    return P08MemoryGate(legacy_store_module, ledger, runtime)
