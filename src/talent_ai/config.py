"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw_value!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Runtime settings with safe defaults suitable for local development."""

    database_path: Path
    host: str
    port: int
    max_upload_bytes: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["database_path"] = str(self.database_path)
        return data


def load_settings() -> Settings:
    """Build settings from the environment, falling back to local defaults."""

    home = Path(
        os.getenv("TALENT_AI_HOME", str(Path.home() / ".talent-ai"))
    ).expanduser()
    default_database = home / "talent.db"
    database_path = Path(
        os.getenv("TALENT_AI_DB", str(default_database))
    ).expanduser()
    return Settings(
        database_path=database_path,
        host=os.getenv("TALENT_AI_HOST", "127.0.0.1"),
        port=_int_env("TALENT_AI_PORT", 8080),
        max_upload_bytes=_int_env("TALENT_AI_MAX_UPLOAD_BYTES", 1_000_000),
    )

