from __future__ import annotations
import subprocess
from core.dependencies import ensure_dependency, get_dynamic_subnet
from core.config import load_settings
from rich.console import Console
console = Console()

def _subnet_from_settings() -> str:
    subnet = load_settings().get("default_subnet", "auto")
    return get_dynamic_subnet() if str(subnet).lower() == "auto" else subnet

def subnet_scan() -> None:
    if not ensure_dependency("nmap"):
        console.print("[red]Nmap is unavailable. Subnet scan cancelled.[/red]")
        return
    default = _subnet_from_settings()
    subnet = input(f"Subnet [{default}]: ").strip() or default
    subprocess.run(["nmap", "-sn", subnet])

def port_scan() -> None:
    if not ensure_dependency("nmap"):
        return
    target = input("Target IP/hostname: ").strip()
    if not target:
        return
    subprocess.run(["nmap", "-sV", target])

def os_fingerprint() -> None:
    if not ensure_dependency("nmap"):
        return
    target = input("Target IP/hostname: ").strip()
    if not target:
        return
    subprocess.run(["nmap", "-O", target])
