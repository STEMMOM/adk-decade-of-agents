# adk_runtime/memory_store.py
from __future__ import annotations
import json
import time
from datetime import datetime
from typing import Any, Dict

from .paths import MEMORY_STORE_FILE, ensure_runtime_dirs
from .events import append_event


DEFAULT_MEMORY: Dict[str, Any] = {
    "schema_version": "1.0",
    "user_profile": {},
    "conversation_summaries": [],
    "meta": {
        "created_by": "Entropy Control OS",
        "notes": "Global long-term memory store (MVP).",
    },
}


def _policy_check_write_proposal(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    P07 v0 — deny-by-default.
    All memory writes are blocked unless explicitly allow-listed.
    """
    return {
        "proposal_id": proposal["proposal_id"],
        "decision": "blocked",
        "rule_hits": [
            {
                "rule_id": "P07-DENY-DEFAULT",
                "severity": "hard",
            }
        ],
        "reason": "P07 v0 deny-by-default: memory writes require explicit allow-list.",
        "policy_version": "policy_gate_v0",
    }


def save_memory(data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    P07: audited memory write.
    """
    ensure_runtime_dirs()
    source = kwargs.get("source", "runtime")
    actor = kwargs.get("actor") or {"agent_id": "system", "persona_id": "default"}

    proposal_id = f"mw_{int(time.time() * 1000)}"
    proposal = {
        "proposal_id": proposal_id,
        "ts": datetime.utcnow().isoformat() + "Z",
        "actor": actor,
        "target": {
            "store": "world_memory",
            "path": str(MEMORY_STORE_FILE),
            "op": "write",
        },
        "value": {
            "type": "json",
            "summary": "memory_store.json",
        },
        "tags": ["scope:world_memory"],
    }

    append_event(
        event_type="memory.write_proposed",
        session_id="memory-store",
        trace_id=proposal_id,
        payload={
            "proposal_id": proposal_id,
            "source": source,
            "actor": actor,
            "proposal": proposal,
        },
    )

    decision = _policy_check_write_proposal(proposal)

    append_event(
        event_type="policy.check",
        session_id="memory-store",
        trace_id=proposal_id,
        payload={
            "proposal_id": proposal_id,
            "source": source,
            "actor": actor,
            "decision": decision,
        },
    )

    if decision["decision"] != "allowed":
        append_event(
            event_type="memory.write_blocked",
            session_id="memory-store",
            trace_id=proposal_id,
            payload={
                "proposal_id": proposal_id,
                "source": source,
                "actor": actor,
                "decision": decision,
            },
        )
        return {
            "status": "blocked",
            "decision": decision,
        }

    _write_memory_file(data)

    append_event(
        event_type="memory.write_committed",
        session_id="memory-store",
        trace_id=proposal_id,
        payload={
            "proposal_id": proposal_id,
            "source": source,
            "actor": actor,
            "decision": decision,
        },
    )

    return {
        "status": "committed",
        "decision": decision,
    }


def load_memory() -> Dict[str, Any]:
    """加载 OS 级长期记忆。不存在则返回默认结构。"""
    ensure_runtime_dirs()
    if not MEMORY_STORE_FILE.exists():
        return DEFAULT_MEMORY.copy()
    with MEMORY_STORE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_memory_file(data: Dict[str, Any]) -> None:
    with MEMORY_STORE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
