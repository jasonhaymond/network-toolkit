from __future__ import annotations
import platform
from rich.console import Console
from core.interrupts import run_process

console = Console()


def run_command(command: list[str], timeout: int | None = 30) -> tuple[int, str, str]:
    result = run_process(command, capture_output=True, timeout=timeout)
    if result is None:
        return 1, "", "Cancelled"
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_linux() -> bool:
    return platform.system() == "Linux"
