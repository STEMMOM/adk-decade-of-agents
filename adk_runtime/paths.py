# adk_runtime/paths.py
from __future__ import annotations
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]

# 假设：adk_runtime/ 位于 repo 根目录下
REPO_ROOT: Path = Path(__file__).resolve().parents[1]

PROJECTS_DIR: Path = REPO_ROOT / "projects"
RUNTIME_DATA_DIR: Path = REPO_ROOT / "runtime_data"
LOGS_DIR: Path = RUNTIME_DATA_DIR / "logs"
EVENTS_FILE: Path = RUNTIME_DATA_DIR / "events.jsonl"
MEMORY_STORE_FILE: Path = RUNTIME_DATA_DIR / "memory_store.json"
GLOBAL_PERSONA_FILE: Path = REPO_ROOT / "persona.json"


def ensure_runtime_dirs() -> None:
    """确保 OS 级运行目录存在。"""
    for p in [RUNTIME_DATA_DIR, LOGS_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def get_project_dir(project_name: str) -> Path:
    return PROJECTS_DIR / project_name


def get_project_src_dir(project_name: str) -> Path:
    return get_project_dir(project_name) / "src"


def get_log_file(name: str = "runtime.log") -> Path:
    return LOGS_DIR / name
