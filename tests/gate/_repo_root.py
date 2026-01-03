from __future__ import annotations

import subprocess
from pathlib import Path


def repo_root() -> Path:
    out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    return Path(out)
