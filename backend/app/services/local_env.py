"""Read selected local settings without mutating process environment."""

from __future__ import annotations

import os
from pathlib import Path


def local_env_value(name: str, default: str = "", root: Path | None = None) -> str:
    process_value = os.getenv(name)
    if process_value is not None:
        return process_value.strip()

    base = root or Path(__file__).resolve().parents[2]
    for path in (base / ".env", base / "env"):
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    return default
