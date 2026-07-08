"""
dependencies.py

Cross-platform dependency manager for Network Toolkit.

This file separates two very different things that humans, package
managers, and Windows PATH handling love to blur together:

1. Python packages installed with pip
2. External command-line tools installed with winget/choco/scoop/brew/apt/etc.

It also knows that some tools are not useful or not supported on every OS,
so the startup audit no longer screams that macOS/Linux-only tools are
"missing" on Windows. Revolutionary. Barely civilized.
"""

from __future__ import annotations

import importlib.util
import ipaddress
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import psutil
from rich.console import Console
from rich.table import Table

console = Console()
SYSTEM = platform.system()  # Windows, Darwin, Linux
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PythonPackage:
    pip_name: str
    import_names: tuple[str, ...]
    description: str
    required: bool = True


@dataclass(frozen=True)
class CommandDependency:
    key: str
    commands: tuple[str, ...]
    description: str
    platforms: tuple[str, ...] = ("Windows", "Darwin", "Linux")
    required: bool = False
    winget_id: str | None = None
    choco_name: str | None = None
    scoop_name: str | None = None
    brew_name: str | None = None
    apt_name: str | None = None
    dnf_name: str | None = None
    pacman_name: str | None = None
    common_windows_paths: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Python package dependencies
# ---------------------------------------------------------------------------

PYTHON_PACKAGES: dict[str, PythonPackage] = {
    "rich": PythonPackage("rich", ("rich",), "Pretty terminal output"),
    "psutil": PythonPackage("psutil", ("psutil",), "Interface and system information"),
    "PyYAML": PythonPackage("PyYAML", ("yaml",), "Settings file support"),
    "requests": PythonPackage("requests", ("requests",), "HTTP checks and public IP lookup"),
    "ping3": PythonPackage("ping3", ("ping3",), "Python ping helper", required=False),
    "speedtest-cli": PythonPackage("speedtest-cli", ("speedtest",), "Internet speed test module", required=False),
    "dnspython": PythonPackage("dnspython", ("dns", "dns.resolver"), "Advanced DNS resolver support", required=False),
    "python-nmap": PythonPackage("python-nmap", ("nmap",), "Python wrapper for Nmap", required=False),
}


# ---------------------------------------------------------------------------
# External command dependencies
# ---------------------------------------------------------------------------

COMMAND_DEPENDENCIES: dict[str, CommandDependency] = {
    "nmap": CommandDependency(
        key="nmap",
        commands=("nmap", "nmap.exe"),
        description="Subnet scans, ping sweeps, port scans, service/OS fingerprinting",
        required=True,
        winget_id="Insecure.Nmap",
        choco_name="nmap",
        scoop_name="nmap",
        brew_name="nmap",
        apt_name="nmap",
        dnf_name="nmap",
        pacman_name="nmap",
        common_windows_paths=(
            r"C:\Program Files (x86)\Nmap\nmap.exe",
            r"C:\Program Files\Nmap\nmap.exe",
        ),
    ),
    "iperf3": CommandDependency(
        key="iperf3",
        commands=("iperf3", "iperf3.exe"),
        description="LAN throughput testing",
        required=False,
        winget_id="ESnet.iPerf3",
        choco_name="iperf3",
        scoop_name="iperf3",
        brew_name="iperf3",
        apt_name="iperf3",
        dnf_name="iperf3",
        pacman_name="iperf3",
        common_windows_paths=(
            r"C:\Program Files\iperf3\iperf3.exe",
            r"C:\Program Files (x86)\iperf3\iperf3.exe",
            r"C:\iperf3\iperf3.exe",
        ),
    ),
    "tcpdump": CommandDependency(
        key="tcpdump",
        commands=("tcpdump",),
        description="Packet capture",
        platforms=("Darwin", "Linux"),
        required=False,
        brew_name=None,  # Built into macOS enough for our purpose.
        apt_name="tcpdump",
        dnf_name="tcpdump",
        pacman_name="tcpdump",
    ),
    "lldpctl": CommandDependency(
        key="lldpctl",
        commands=("lldpctl",),
        description="LLDP switch and port discovery",
        platforms=("Darwin", "Linux"),
        required=False,
        brew_name="lldpd",
        apt_name="lldpd",
        dnf_name="lldpd",
        pacman_name="lldpd",
    ),
    "arp-scan": CommandDependency(
        key="arp-scan",
        commands=("arp-scan",),
        description="ARP-based subnet discovery",
        platforms=("Darwin", "Linux"),
        required=False,
        brew_name="arp-scan",
        apt_name="arp-scan",
        dnf_name="arp-scan",
        pacman_name="arp-scan",
    ),
    "tshark": CommandDependency(
        key="tshark",
        commands=("tshark", "tshark.exe"),
        description="Advanced packet capture/inspection via Wireshark CLI",
        required=False,
        winget_id="WiresharkFoundation.Wireshark",
        choco_name="wireshark",
        brew_name="wireshark",
        apt_name="tshark",
        dnf_name="wireshark-cli",
        pacman_name="wireshark-cli",
        common_windows_paths=(
            r"C:\Program Files\Wireshark\tshark.exe",
            r"C:\Program Files (x86)\Wireshark\tshark.exe",
        ),
    ),
}


# Backward-compatible names older modules may import.
DEPENDENCIES = COMMAND_DEPENDENCIES


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def _split_path() -> list[str]:
    return [p for p in os.environ.get("PATH", "").split(os.pathsep) if p]


def _add_to_path(directory: str | Path) -> None:
    directory = str(directory)
    if not directory:
        return
    existing = _split_path()
    if directory not in existing:
        os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")


def _candidate_project_tool_paths(command: str) -> Iterable[Path]:
    """Look for portable tools bundled inside the project folder."""
    names = {command, f"{command}.exe"}
    for folder in (
        PROJECT_ROOT / "tools",
        PROJECT_ROOT / "bin",
        PROJECT_ROOT / "vendor",
    ):
        if not folder.exists():
            continue
        for name in names:
            yield folder / name
        if SYSTEM == "Windows":
            # A small recursive search for common portable layouts.
            for name in names:
                yield from folder.glob(f"**/{name}")


def resolve_command(command_or_key: str) -> str | None:
    """
    Return an executable path/name for a command dependency.

    This does more than shutil.which because Windows installers often add PATH
    only for newly opened terminals. If we can find the executable in common
    locations, we add its folder to this process PATH so subprocess calls work.
    """
    dep = COMMAND_DEPENDENCIES.get(command_or_key)
    command_names = dep.commands if dep else (command_or_key,)

    for command in command_names:
        found = shutil.which(command)
        if found:
            return found

    # Portable project-local tools.
    for command in command_names:
        for candidate in _candidate_project_tool_paths(command.removesuffix(".exe")):
            if candidate.exists() and candidate.is_file():
                _add_to_path(candidate.parent)
                return str(candidate)

    # Known Windows install locations.
    if SYSTEM == "Windows" and dep:
        for raw_path in dep.common_windows_paths:
            candidate = Path(os.path.expandvars(raw_path))
            if candidate.exists() and candidate.is_file():
                _add_to_path(candidate.parent)
                return str(candidate)

    return None


def command_exists(command_or_key: str) -> bool:
    return resolve_command(command_or_key) is not None


def require_command(command_or_key: str) -> bool:
    return ensure_dependency(command_or_key)


def python_package_exists(package: PythonPackage) -> bool:
    return all(importlib.util.find_spec(name) is not None for name in package.import_names)


def _run(command: list[str]) -> bool:
    try:
        result = subprocess.run(command)
        return result.returncode == 0
    except Exception as exc:
        console.print(f"[red]Command failed:[/red] {' '.join(command)}")
        console.print(str(exc))
        return False


# ---------------------------------------------------------------------------
# Python package installation
# ---------------------------------------------------------------------------

def install_python_package(pip_name: str) -> bool:
    console.print(f"[cyan]Installing Python package:[/cyan] {pip_name}")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", pip_name])
    return result.returncode == 0


def install_python_requirements() -> bool:
    requirements = PROJECT_ROOT / "requirements.txt"
    if not requirements.exists():
        console.print("[yellow]requirements.txt was not found.[/yellow]")
        return False
    console.print("[cyan]Installing/updating Python requirements...[/cyan]")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r", str(requirements)])
    return result.returncode == 0


def ensure_python_package(import_or_pip_name: str, pip_name: str | None = None) -> bool:
    """Backward-compatible helper for older code."""
    package = PYTHON_PACKAGES.get(import_or_pip_name)
    if package is None:
        package = next((p for p in PYTHON_PACKAGES.values() if import_or_pip_name in p.import_names), None)
    if package is None:
        package = PythonPackage(pip_name or import_or_pip_name, (import_or_pip_name,), "Python package")

    if python_package_exists(package):
        return True

    answer = input(f"Install Python package {package.pip_name}? (Y/n): ").strip().lower()
    if answer not in ("", "y", "yes"):
        return False

    install_python_package(package.pip_name)
    return python_package_exists(package)


# ---------------------------------------------------------------------------
# External package manager detection and installation
# ---------------------------------------------------------------------------

def available_package_managers() -> list[str]:
    managers: list[str] = []
    if SYSTEM == "Windows":
        for manager in ("winget", "choco", "scoop"):
            if shutil.which(manager):
                managers.append(manager)
    elif SYSTEM == "Darwin":
        if shutil.which("brew"):
            managers.append("brew")
    elif SYSTEM == "Linux":
        for manager in ("apt", "dnf", "pacman"):
            if shutil.which(manager):
                managers.append(manager)
    return managers


def _install_command_for(dep: CommandDependency, manager: str) -> list[str] | None:
    if manager == "winget" and dep.winget_id:
        return ["winget", "install", "-e", "--id", dep.winget_id]
    if manager == "choco" and dep.choco_name:
        return ["choco", "install", dep.choco_name, "-y"]
    if manager == "scoop" and dep.scoop_name:
        return ["scoop", "install", dep.scoop_name]
    if manager == "brew" and dep.brew_name:
        return ["brew", "install", dep.brew_name]
    if manager == "apt" and dep.apt_name:
        return ["sudo", "apt", "install", "-y", dep.apt_name]
    if manager == "dnf" and dep.dnf_name:
        return ["sudo", "dnf", "install", "-y", dep.dnf_name]
    if manager == "pacman" and dep.pacman_name:
        return ["sudo", "pacman", "-S", "--noconfirm", dep.pacman_name]
    return None


def install_dependency(name: str) -> bool:
    dep = COMMAND_DEPENDENCIES.get(name) or next(
        (d for d in COMMAND_DEPENDENCIES.values() if name in d.commands),
        None,
    )

    if dep is None:
        console.print(f"[yellow]No installer definition exists for '{name}'.[/yellow]")
        return False

    if SYSTEM not in dep.platforms:
        console.print(f"[yellow]{dep.key} is not supported by this toolkit on {SYSTEM} yet.[/yellow]")
        return False

    if command_exists(dep.key):
        return True

    managers = available_package_managers()
    if not managers:
        console.print("[yellow]No supported package manager was found.[/yellow]")
        if SYSTEM == "Windows":
            console.print("Install winget, Chocolatey, or Scoop, or install the tool manually.")
        return False

    for manager in managers:
        install_cmd = _install_command_for(dep, manager)
        if install_cmd is None:
            continue
        console.print(f"\n[cyan]Installing {dep.key} with {manager}...[/cyan]")
        if _run(install_cmd):
            if command_exists(dep.key):
                console.print(f"[green]{dep.key} is ready.[/green]")
                return True
            console.print(f"[yellow]{dep.key} may be installed, but it is not visible in this terminal yet.[/yellow]")
            console.print("Close and reopen VS Code/Terminal if it still shows missing. Yes, PATH is still ridiculous.")
            return False

    console.print(f"[red]Automatic installation failed or no installer is defined for {dep.key}.[/red]")
    return False


def ensure_dependency(name: str) -> bool:
    dep = COMMAND_DEPENDENCIES.get(name) or next(
        (d for d in COMMAND_DEPENDENCIES.values() if name in d.commands),
        None,
    )
    display_name = dep.key if dep else name

    if command_exists(display_name):
        return True

    if dep and SYSTEM not in dep.platforms:
        console.print(f"[yellow]{display_name} is not supported on {SYSTEM} in this toolkit.[/yellow]")
        return False

    console.print(f"\n[yellow]{display_name} is not installed or not in PATH.[/yellow]")
    answer = input("Install automatically now? (Y/n): ").strip().lower()
    if answer in ("", "y", "yes"):
        return install_dependency(display_name)
    return False


# ---------------------------------------------------------------------------
# Status and startup audit
# ---------------------------------------------------------------------------

def python_dependency_status() -> list[tuple[str, str, bool, str]]:
    rows: list[tuple[str, str, bool, str]] = []
    for package in PYTHON_PACKAGES.values():
        installed = python_package_exists(package)
        rows.append((package.pip_name, "Python", installed, package.description))
    return rows


def command_dependency_status() -> list[tuple[str, str, bool | None, str]]:
    rows: list[tuple[str, str, bool | None, str]] = []
    for dep in COMMAND_DEPENDENCIES.values():
        if SYSTEM not in dep.platforms:
            rows.append((dep.key, "External", None, f"Unsupported on {SYSTEM}: {dep.description}"))
        else:
            rows.append((dep.key, "External", command_exists(dep.key), dep.description))
    return rows


def dependency_status(show_python: bool = True) -> list[tuple[str, str, bool | None, str]]:
    rows: list[tuple[str, str, bool | None, str]] = []
    if show_python:
        rows.extend(python_dependency_status())
    rows.extend(command_dependency_status())
    return rows


def print_dependency_status() -> None:
    table = Table(title="Network Toolkit Dependency Status")
    table.add_column("Dependency")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Use")

    for name, dep_type, installed, desc in dependency_status(show_python=True):
        if installed is True:
            status = "[green]Installed[/green]"
        elif installed is False:
            status = "[red]Missing[/red]"
        else:
            status = "[dim]N/A[/dim]"
        table.add_row(name, dep_type, status, desc)

    console.print(table)


def startup_dependency_audit(auto_install_mode: str = "ask") -> None:
    """
    Run one clean startup dependency check.

    auto_install_mode:
        ask    - ask before installing
        always - install without asking
        never  - only report
    """
    console.print("\n[cyan]Network Toolkit Startup Check[/cyan]")
    console.print("Checking Python packages and external tools. The least glamorous part of civilization.\n")

    print_dependency_status()

    missing_python = [p for p in PYTHON_PACKAGES.values() if not python_package_exists(p)]
    missing_commands = [
        d for d in COMMAND_DEPENDENCIES.values()
        if SYSTEM in d.platforms and not command_exists(d.key)
    ]

    if not missing_python and not missing_commands:
        console.print("[green]All known dependencies are available.[/green]")
        return

    console.print(f"\n[yellow]{len(missing_python) + len(missing_commands)} supported dependencies are missing.[/yellow]")

    if auto_install_mode == "never":
        return

    install = auto_install_mode == "always"
    if auto_install_mode == "ask":
        answer = input("Install/update missing supported dependencies now? (Y/n): ").strip().lower()
        install = answer in ("", "y", "yes")

    if not install:
        return

    if missing_python:
        # Use requirements.txt first because it is simpler and keeps versions sane.
        install_python_requirements()
        for package in missing_python:
            if not python_package_exists(package):
                install_python_package(package.pip_name)

    for dep in missing_commands:
        install_dependency(dep.key)

    console.print("\n[cyan]Rechecking dependency status...[/cyan]")
    print_dependency_status()


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def get_dynamic_subnet() -> str:
    """
    Return the subnet for the first active non-loopback IPv4 interface.
    Example: 192.168.1.0/24
    """
    for interface, addresses in psutil.net_if_addrs().items():
        for addr in addresses:
            if addr.family != socket.AF_INET:
                continue
            if addr.address.startswith("127."):
                continue
            if not addr.netmask:
                continue
            try:
                network = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
                return str(network)
            except Exception:
                continue
    return "192.168.1.0/24"
