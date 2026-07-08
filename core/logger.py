from __future__ import annotations
from datetime import datetime
from pathlib import Path
from core.config import BASE_DIR, load_settings

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def log(message: str) -> None:
    settings = load_settings()
    if not settings.get("logging_enabled", True):
        return
    logfile = LOG_DIR / f"{datetime.now():%Y-%m-%d}.log"
    with logfile.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")
