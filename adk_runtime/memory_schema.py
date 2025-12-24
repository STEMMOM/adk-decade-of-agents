from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class MemoryZone(str, Enum):
    WORLD_STATE = "world_state"
    DECISION_ACTION = "decision_action"
    OBSERVATION = "observation"
    LEGACY = "legacy"


class ValidationError(Exception):
    """Raised when a memory write violates schema/version/zone rules."""


@dataclass(frozen=True)
class RuntimeSchema:
    # P08 v0: runtime supports exactly one "current" schema generation
    supported_schema_version: int = 0
    supported_store_version: int = 0


def _provenance_ok(prov: Optional[Dict[str, Any]]) -> bool:
    """
    P08 v0 minimal provenance for World State.
    We accept a coarse source_type classification.
    """
    if not prov or not isinstance(prov, dict):
        return False
    source_type = prov.get("source_type")
    allowed = {"user_declared", "tool_verified", "human_approved"}
    return source_type in allowed


def validate_memory_entry(entry: Dict[str, Any], runtime: RuntimeSchema) -> None:
    """
    Enforces P08 v0 invariants:
      - schema_version required
      - zone required
      - legacy is read-only
      - unsupported future schema blocks
      - observation -> world_state promotion requires explicit authorization (v0: block)
      - world_state requires provenance
      - decision_action is append-only (enforced at store level by not allowing update APIs)
    """
    if "schema_version" not in entry:
        raise ValidationError("UC-01: missing schema_version")
    if not isinstance(entry["schema_version"], int):
        raise ValidationError("schema_version must be int")

    schema_version = entry["schema_version"]

    # UC-05: future schema not supported
    if schema_version > runtime.supported_schema_version:
        raise ValidationError("UC-05: unsupported future schema_version")

    if "zone" not in entry:
        raise ValidationError("UC-02: missing zone")
    try:
        zone = MemoryZone(entry["zone"])
    except Exception:
        raise ValidationError(f"invalid zone: {entry.get('zone')}")

    # UC-03: cannot write to legacy zone
    if zone == MemoryZone.LEGACY:
        raise ValidationError("UC-03: cannot write to legacy zone")

    # UC-07: world_state requires provenance
    if zone == MemoryZone.WORLD_STATE:
        if not _provenance_ok(entry.get("provenance")):
            raise ValidationError("UC-07: world_state requires minimal provenance")

    # UC-06: observation to world_state promotion requires explicit authorization
    # v0: simplest rule — if entry claims it is a promotion, block unless allowlist flag present.
    if entry.get("promotion_from") is not None:
        # In v0, require an explicit boolean authorization token.
        if entry.get("promotion_authorized") is not True:
            raise ValidationError("UC-06: promotion to world_state requires explicit authorization")

    # P08 v0: require zone responsibility declared; done above.
    # P08 v0: do not infer zone from content; this function never infers.

