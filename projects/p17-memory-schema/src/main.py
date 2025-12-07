#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目 17：Memory Schema v1（长期记忆架构化）
-----------------------------------------
目标：
1. 为 Agent 的长期记忆定义一个正式的 Schema（version 1.0）
2. 从现有的 memory_store.json（例如从 P16 复制过来）加载“老记忆”
3. 将老格式（平铺 key-value + conversation_summaries）升级为：

   {
     "schema_version": "1.0",
     "user_profile": {...},
     "conversation_summaries": [...],
     "preferences": [...],
     "knowledge": [...]
   }

4. 写回同一个 memory_store.json（就地升级），作为后续 Persona / Scheduler 的基础

运行方式（在项目目录下）：
    (.venv) cd projects/p17-memory-schema
    (.venv) python src/main.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---- 路径与全局常量 ----
APP_NAME = "agents"
USER_ID = "susan"

# 当前文件：projects/p17-memory-schema/src/main.py
BASE_DIR = Path(__file__).resolve().parent.parent  # projects/p17-memory-schema
MEMORY_FILE = BASE_DIR / "memory_store.json"       # 输入 + 输出：同一个文件，就地升级
LEGACY_MEMORY_FILE = MEMORY_FILE                   # 为语义清晰单独命名，但指向同一路径


# =====================================
#         Memory Schema v1 定义
# =====================================

MEMORY_SCHEMA_V1: Dict[str, Any] = {
    "schema_version": "1.0",
    "channels": {
        "user_profile": {
            "description": "Core identity & stable attributes of the user",
            "key_prefix": "user:",  # 使用 key 前缀从旧结构中抽取
        },
        "conversation_summaries": {
            "description": "Structured topic-level summaries produced via compaction",
            "fields": ["app_name", "user_id", "session_id", "created_at", "summary_text", "raw"],
        },
        "preferences": {
            "description": "Learned user preferences (to be populated in later projects)",
            "fields": ["key", "value", "confidence", "source"],
        },
        "knowledge": {
            "description": "Facts or structured knowledge extracted from dialogues",
            "fields": ["fact", "source_session", "created_at"],
        },
    },
    "merge_rules": {
        "user_profile": "replace",
        "conversation_summaries": "append",
        "preferences": "update_or_append",
        "knowledge": "append",
    },
    "timestamp_format": "ISO8601",
}


# =====================================
#         基础读写函数
# =====================================

def load_legacy_memory() -> Dict[str, Any]:
    """
    从现有的 memory_store.json 加载“老记忆”。
    如果不存在，则返回空 dict。
    """
    print(f"📥 Loading legacy memory from: {LEGACY_MEMORY_FILE}")
    if not LEGACY_MEMORY_FILE.exists():
        print("⚠️ No existing memory_store.json found. Starting from empty legacy memory.")
        return {}

    try:
        with LEGACY_MEMORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                print("✅ Legacy memory loaded successfully.")
                return data
            print("⚠️ Legacy memory is not a dict. Using empty legacy structure.")
            return {}
    except Exception as e:
        print("⚠️ Failed to read legacy memory. Using empty legacy structure:", repr(e))
        return {}


def save_memory_v1(memory_v1: Dict[str, Any]) -> None:
    """
    将 Schema v1 结构写回 memory_store.json（就地覆盖）。
    """
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(memory_v1, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved Memory Schema v1 to: {MEMORY_FILE}")


# =====================================
#        Schema v1 升级核心逻辑
# =====================================

def upgrade_to_schema_v1(legacy: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    将旧 memory_store.json 升级为 Schema v1 结构。

    输入：
        legacy: 旧格式的内存（可能是平铺 key-value，也可能已经有 conversation_summaries 列表）

    输出：
        (memory_v1, debug_info)
        - memory_v1: 新的 Schema v1 结构
        - debug_info: 升级过程的一些统计信息（方便调试与审计）
    """
    debug_info: Dict[str, Any] = {
        "user_profile_keys": [],
        "conversation_summaries_count": 0,
        "legacy_top_level_keys": list(legacy.keys()),
    }

    # 初始化新结构
    memory_v1: Dict[str, Any] = {
        "schema_version": MEMORY_SCHEMA_V1["schema_version"],
        "user_profile": {},
        "conversation_summaries": [],
        "preferences": [],
        "knowledge": [],
    }

    # 1) user_profile：从 legacy 中抽取所有以 "user:" 开头的 key
    user_profile: Dict[str, Any] = {}

    for k, v in legacy.items():
        # 跳过旧的 conversation_summaries（它会在后面单独处理）
        if k == "conversation_summaries":
            continue

        if isinstance(k, str) and k.startswith("user:"):
            # user:name -> name
            key_name = k.split("user:", 1)[1]
            user_profile[key_name] = v
            debug_info["user_profile_keys"].append(k)

    memory_v1["user_profile"] = user_profile

    # 2) conversation_summaries：如果旧结构中已有，则做 fields 规范化后迁移
    legacy_summaries = legacy.get("conversation_summaries", [])
    if isinstance(legacy_summaries, list):
        normalized_summaries: List[Dict[str, Any]] = []
        for item in legacy_summaries:
            if not isinstance(item, dict):
                continue
            normalized = {
                "app_name": item.get("app_name", APP_NAME),
                "user_id": item.get("user_id", USER_ID),
                "session_id": item.get("session_id"),
                "created_at": item.get("created_at"),
                "summary_text": item.get("summary_text"),
                "raw": item.get("raw", {}),
            }
            normalized_summaries.append(normalized)

        memory_v1["conversation_summaries"] = normalized_summaries
        debug_info["conversation_summaries_count"] = len(normalized_summaries)

    # 3) preferences / knowledge：P17 先留空，后续项目（P18+）填充
    #    在本项目中，我们只负责把已有两类长期记忆（user_profile & conversation_summaries）正规化。

    return memory_v1, debug_info


# =====================================
#              打印函数
# =====================================

def print_schema_v1(memory_v1: Dict[str, Any], debug_info: Dict[str, Any]) -> None:
    """打印升级结果的摘要信息（方便在终端快速确认效果）。"""
    print("\n🧬 Memory Schema v1 upgrade summary")
    print("-----------------------------------")
    print(f"schema_version: {memory_v1.get('schema_version')}")
    print(f"user_profile keys: {list(memory_v1.get('user_profile', {}).keys())}")
    print(f"conversation_summaries count: {len(memory_v1.get('conversation_summaries', []))}")
    print(f"preferences count: {len(memory_v1.get('preferences', []))}")
    print(f"knowledge count: {len(memory_v1.get('knowledge', []))}")

    print("\n🔍 Debug Info:")
    print(f"- legacy top-level keys: {debug_info.get('legacy_top_level_keys')}")
    print(f"- extracted user_profile keys (legacy): {debug_info.get('user_profile_keys')}")
    print(f"- conversation_summaries migrated: {debug_info.get('conversation_summaries_count')}")

    print("\n📚 Memory Schema v1 (truncated preview):")
    preview = json.dumps(memory_v1, ensure_ascii=False, indent=2)
    print(preview[:1000], "...\n")


# =====================================
#               主逻辑
# =====================================

def main():
    print("🚀 memory_schema_v1: main() started")
    print("🎯 Goal: upgrade existing memory_store.json into Memory Schema v1\n")

    # Step 1: 加载旧 Memory
    legacy = load_legacy_memory()

    print("\n📦 Legacy memory (truncated preview):")
    legacy_preview = json.dumps(legacy, ensure_ascii=False, indent=2)
    print(legacy_preview[:800], "...\n")

    # Step 2: 升级为 Schema v1
    memory_v1, debug_info = upgrade_to_schema_v1(legacy)

    # Step 3: 写回新的 Memory（就地覆盖）
    save_memory_v1(memory_v1)

    # Step 4: 打印摘要结果
    print_schema_v1(memory_v1, debug_info)

    print("🏁 memory_schema_v1: main() finished")


if __name__ == "__main__":
    print("👉 Running Memory Schema v1 upgrader via __main__")
    try:
        main()
    except Exception as e:
        print("❌ Program error:", repr(e))
