from __future__ import annotations

import os
import shlex
import signal
import subprocess
import time
from collections.abc import Callable
from typing import Any

from rich.console import Console

console = Console()


class OperationCancelled(Exception):
    """Raised when the user cancels the current operation with Ctrl+C."""


def prompt_input(prompt: str = "") -> str:
    """input() wrapper that turns Ctrl+C into a controlled menu return."""
    try:
        return input(prompt)
    except KeyboardInterrupt as exc:
        raise OperationCancelled from exc


def cancel_message(message: str = "Cancelled. Returning to previous menu.") -> None:
    console.print(f"\n[yellow]{message}[/yellow]")


def run_menu_action(action: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
    """Run a menu action. Return True when cancelled, False otherwise."""
    try:
        action(*args, **kwargs)
        return False
    except OperationCancelled:
        cancel_message()
        return True
    except KeyboardInterrupt:
        cancel_message()
        return True


def run_process(
    command: list[str],
    *,
    timeout: int | float | None = None,
    capture_output: bool = False,
    text: bool = True,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    cancel_label: str = "operation",
) -> subprocess.CompletedProcess[str] | None:
    """
    Ctrl+C-safe subprocess runner.

    Unlike subprocess.run(), this does not let Ctrl+C kill the whole toolkit.
    It terminates the child process, then raises OperationCancelled so the caller
    can return to the previous menu. Astonishingly, users like software that
    stops one task without detonating the entire program.
    """
    console.print(f"[dim]{' '.join(shlex.quote(str(part)) for part in command)}[/dim]")

    process: subprocess.Popen[str] | None = None
    start = time.time()

    stdout_pipe = subprocess.PIPE if capture_output else None
    stderr_pipe = subprocess.PIPE if capture_output else None

    try:
        process = subprocess.Popen(
            command,
            stdout=stdout_pipe,
            stderr=stderr_pipe,
            text=text,
            cwd=cwd,
            env=env,
        )

        while process.poll() is None:
            if timeout is not None and (time.time() - start) >= float(timeout):
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return subprocess.CompletedProcess(command, 124, "" if capture_output else None, "Command timed out" if capture_output else None)
            time.sleep(0.1)

        if capture_output:
            out, err = process.communicate()
            return subprocess.CompletedProcess(command, process.returncode or 0, out, err)

        return subprocess.CompletedProcess(command, process.returncode or 0, None, None)

    except KeyboardInterrupt as exc:
        if process and process.poll() is None:
            try:
                if os.name == "nt":
                    process.terminate()
                else:
                    process.send_signal(signal.SIGINT)
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        raise OperationCancelled(f"Cancelled {cancel_label}") from exc

    except FileNotFoundError:
        if capture_output:
            return subprocess.CompletedProcess(command, 127, "", f"Command not found: {command[0]}")
        console.print(f"[red]Command not found:[/red] {command[0]}")
        return subprocess.CompletedProcess(command, 127, None, None)
