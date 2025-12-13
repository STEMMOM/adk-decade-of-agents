# adk_runtime/persona_engine.py
from __future__ import annotations
import json
from typing import Any, Dict

from .paths import GLOBAL_PERSONA_FILE


DEFAULT_PERSONA: Dict[str, Any] = {
    "schema_version": "1.0",
    "user_id": "default-user",
    "name": "Unknown User",
    "locale": "en-US",
    "description": "Default persona. Please customize persona.json at repo root.",
    "preferences": {
        "answer_style": "concise_structured",
        "languages": ["en"],
    },
}


def load_persona(user_id: str | None = None) -> Dict[str, Any]:
    """
    加载 persona。
    MVP 版本：
    - 忽略 user_id，直接读取全局 persona.json
    - 如果不存在则返回 DEFAULT_PERSONA
    """
    if not GLOBAL_PERSONA_FILE.exists():
        return DEFAULT_PERSONA.copy()

    with GLOBAL_PERSONA_FILE.open("r", encoding="utf-8") as f:
        persona = json.load(f)

    # 可以在这里做一点最小校验 / 补默认值
    persona.setdefault("schema_version", "1.0")
    if user_id:
        persona.setdefault("user_id", user_id)
    return persona
