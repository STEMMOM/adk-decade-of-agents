from __future__ import annotations

import os
import subprocess
from pathlib import Path


FORBIDDEN_PATH_PREFIXES = (
    ".venv/",
    "venv/",
    "ENV/",
    "runtime_data/",
)

FORBIDDEN_SUBSTRINGS = (
    "/__pycache__/",
)

FORBIDDEN_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".pyd",
)


def _git_ls_files() -> list[str]:
    # List tracked files (index), not untracked files.
    out = subprocess.check_output(["git", "ls-files"], text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def test_repo_hygiene_no_runtime_or_venv_tracked() -> None:
    tracked = _git_ls_files()

    offenders: list[str] = []
    for p in tracked:
        # Normalize to forward slashes
        p_norm = p.replace("\\", "/")

        if p_norm.startswith(FORBIDDEN_PATH_PREFIXES):
            offenders.append(p)

        if any(s in p_norm for s in FORBIDDEN_SUBSTRINGS):
            offenders.append(p)

        if any(p_norm.endswith(suf) for suf in FORBIDDEN_SUFFIXES):
            offenders.append(p)

    # De-dup while keeping order
    seen = set()
    offenders = [x for x in offenders if not (x in seen or seen.add(x))]

    assert not offenders, (
        "Repo hygiene violation: runtime/venv artifacts are tracked by git.\n"
        "Remove them from the index (git rm --cached) and ensure .gitignore blocks them.\n"
        "Offenders (first 50):\n"
        + "\n".join(offenders[:50])
        + ("\n... (truncated)" if len(offenders) > 50 else "")
    )


def test_gitignore_has_must_have_rules() -> None:
    gi = Path(".gitignore")
    assert gi.exists(), ".gitignore missing"

    content = gi.read_text()

    # Minimum "must have" patterns. Keep these aligned with your repo policy.
    must_have = [
        "__pycache__/",
        "*.py[cod]",
        ".venv/",
        "runtime_data/",
    ]

    missing = [p for p in must_have if p not in content]
    assert not missing, f".gitignore missing required patterns: {missing}"
