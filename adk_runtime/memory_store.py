# adk_runtime/memory_store.py
from __future__ import annotations
import json
from typing import Any, Dict

from .paths import MEMORY_STORE_FILE, ensure_runtime_dirs


DEFAULT_MEMORY: Dict[str, Any] = {
    "schema_version": "1.0",
    "user_profile": {},
    "conversation_summaries": [],
    "meta": {
        "created_by": "Entropy Control OS",
        "notes": "Global long-term memory store (MVP).",
    },
}


def load_memory() -> Dict[str, Any]:
    """加载 OS 级长期记忆。不存在则返回默认结构。"""
    ensure_runtime_dirs()
    if not MEMORY_STORE_FILE.exists():
        return DEFAULT_MEMORY.copy()
    with MEMORY_STORE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(data: Dict[str, Any]) -> None:
    """保存 OS 级长期记忆到 runtime_data/memory_store.json。"""
    ensure_runtime_dirs()
    with MEMORY_STORE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
