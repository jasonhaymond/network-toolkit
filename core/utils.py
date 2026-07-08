from __future__ import annotations
import subprocess
import platform
from rich.console import Console

console = Console()

def run_command(command: list[str], timeout: int | None = 30) -> tuple[int, str, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def is_windows() -> bool:
    return platform.system() == "Windows"

def is_macos() -> bool:
    return platform.system() == "Darwin"

def is_linux() -> bool:
    return platform.system() == "Linux"
