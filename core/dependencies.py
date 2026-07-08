"""
dependencies.py

Cross-platform dependency manager for Network Toolkit.
Handles external commands, startup audit, automatic install where possible,
and dynamic subnet detection.
"""
from __future__ import annotations

import importlib
import ipaddress
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

import psutil
from rich.console import Console
from rich.table import Table

console = Console()
SYSTEM = platform.system()

@dataclass(frozen=True)
class Dependency:
    command: str
    description: str
    required: bool = False
    winget_id: str | None = None
    brew_name: str | None = None
    apt_name: str | None = None

DEPENDENCIES: dict[str, Dependency] = {
    "nmap": Dependency("nmap", "Subnet scans, ping sweeps, port scans, OS/service fingerprinting", True, "Insecure.Nmap", "nmap", "nmap"),
    "iperf3": Dependency("iperf3", "Local LAN throughput testing", False, "ESnet.iPerf3", "iperf3", "iperf3"),
    "tcpdump": Dependency("tcpdump", "Packet capture", False, None, None, "tcpdump"),
    "lldpctl": Dependency("lldpctl", "LLDP switch and port discovery", False, None, "lldpd", "lldpd"),
    "speedtest": Dependency("speedtest", "Ookla Speedtest CLI if installed", False, "Ookla.Speedtest.CLI", "speedtest-cli", None),
    "arp-scan": Dependency("arp-scan", "ARP-based subnet discovery", False, None, "arp-scan", "arp-scan"),
}

PYTHON_PACKAGES = {
    "rich": "rich",
    "psutil": "psutil",
    "yaml": "PyYAML",
    "ping3": "ping3",
    "requests": "requests",
}

def command_exists(command: str) -> bool:
    return shutil.which(command) is not None

def require_command(command: str) -> bool:
    return ensure_dependency(command)

def _run(command: list[str]) -> bool:
    try:
        result = subprocess.run(command)
        return result.returncode == 0
    except Exception as exc:
        console.print(f"[red]Command failed:[/red] {' '.join(command)}")
        console.print(str(exc))
        return False

def package_manager() -> str | None:
    if SYSTEM == "Windows" and command_exists("winget"):
        return "winget"
    if SYSTEM == "Darwin" and command_exists("brew"):
        return "brew"
    if SYSTEM == "Linux" and command_exists("apt"):
        return "apt"
    return None

def _install_command_for(dep: Dependency) -> list[str] | None:
    manager = package_manager()
    if manager == "winget" and dep.winget_id:
        return ["winget", "install", "-e", "--id", dep.winget_id]
    if manager == "brew" and dep.brew_name:
        return ["brew", "install", dep.brew_name]
    if manager == "apt" and dep.apt_name:
        return ["sudo", "apt", "install", "-y", dep.apt_name]
    return None

def install_dependency(name: str) -> bool:
    dep = DEPENDENCIES.get(name) or next((d for d in DEPENDENCIES.values() if d.command == name), None)
    if dep is None:
        console.print(f"[yellow]No installer definition exists for '{name}'.[/yellow]")
        return False
    if command_exists(dep.command):
        return True
    install_cmd = _install_command_for(dep)
    if install_cmd is None:
        console.print(f"[yellow]No automatic installer is available for {dep.command} on this system.[/yellow]")
        console.print("Install it manually and restart the terminal. Because PATH enjoys practical jokes.")
        return False
    console.print(f"\n[cyan]Installing {dep.command}...[/cyan]")
    success = _run(install_cmd)
    if not success:
        console.print(f"[red]Installation failed for {dep.command}.[/red]")
        return False
    if command_exists(dep.command):
        console.print(f"[green]{dep.command} is ready.[/green]")
        return True
    console.print(f"[yellow]{dep.command} installed, but it is not visible in this terminal PATH yet.[/yellow]")
    console.print("Close and reopen VS Code/Terminal, then try again.")
    return False

def ensure_dependency(name: str) -> bool:
    dep = DEPENDENCIES.get(name) or next((d for d in DEPENDENCIES.values() if d.command == name), None)
    command = dep.command if dep else name
    if command_exists(command):
        return True
    console.print(f"\n[yellow]{command} is not installed or not in PATH.[/yellow]")
    answer = input("Install automatically now? (Y/n): ").strip().lower()
    if answer in ("", "y", "yes"):
        return install_dependency(name)
    return False

def ensure_python_package(import_name: str, pip_name: str | None = None) -> bool:
    pip_name = pip_name or import_name
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        console.print(f"[yellow]Python package missing:[/yellow] {pip_name}")
        answer = input("Install automatically now? (Y/n): ").strip().lower()
        if answer not in ("", "y", "yes"):
            return False
        result = subprocess.run([sys.executable, "-m", "pip", "install", pip_name])
        return result.returncode == 0

def dependency_status(show_python: bool = True) -> list[tuple[str, bool, str]]:
    rows: list[tuple[str, bool, str]] = []
    for dep in DEPENDENCIES.values():
        rows.append((dep.command, command_exists(dep.command), dep.description))
    if show_python:
        for import_name, pip_name in PYTHON_PACKAGES.items():
            try:
                importlib.import_module(import_name)
                ok = True
            except ImportError:
                ok = False
            rows.append((pip_name, ok, "Python package"))
    return rows

def print_dependency_status() -> None:
    table = Table(title="Network Toolkit Dependency Status")
    table.add_column("Dependency")
    table.add_column("Status")
    table.add_column("Use")
    for name, installed, desc in dependency_status():
        status = "[green]Installed[/green]" if installed else "[red]Missing[/red]"
        table.add_row(name, status, desc)
    console.print(table)

def startup_dependency_audit(auto_install_mode: str = "ask") -> None:
    console.print("\n[cyan]Network Toolkit Startup Check[/cyan]")
    console.print("Checking dependencies, because apparently computers require ingredients now.\n")
    print_dependency_status()
    missing_commands = [name for name, ok, _ in dependency_status(show_python=False) if not ok]
    missing_python = []
    for import_name, pip_name in PYTHON_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing_python.append((import_name, pip_name))
    if not missing_commands and not missing_python:
        console.print("[green]All known dependencies are available.[/green]")
        return
    console.print(f"\n[yellow]{len(missing_commands) + len(missing_python)} dependencies are missing.[/yellow]")
    install = False
    if auto_install_mode == "always":
        install = True
    elif auto_install_mode == "never":
        install = False
    else:
        answer = input("Install missing supported dependencies now? (Y/n): ").strip().lower()
        install = answer in ("", "y", "yes")
    if not install:
        return
    for import_name, pip_name in missing_python:
        subprocess.run([sys.executable, "-m", "pip", "install", pip_name])
    for name in missing_commands:
        install_dependency(name)
    console.print("\n[cyan]Rechecking dependency status...[/cyan]")
    print_dependency_status()

def get_dynamic_subnet() -> str:
    for interface, addresses in psutil.net_if_addrs().items():
        for addr in addresses:
            if addr.family != socket.AF_INET:
                continue
            if addr.address.startswith("127."):
                continue
            if not addr.netmask:
                continue
            network = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
            return str(network)
    return "192.168.1.0/24"
