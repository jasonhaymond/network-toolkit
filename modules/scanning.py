from __future__ import annotations
from core.dependencies import ensure_dependency, get_dynamic_subnet, resolve_command
from core.config import load_settings
from rich.console import Console
from core.interrupts import prompt_input, run_process
console = Console()

def _subnet_from_settings() -> str:
    subnet = load_settings().get("default_subnet", "auto")
    return get_dynamic_subnet() if str(subnet).lower() == "auto" else subnet

def subnet_scan() -> None:
    if not ensure_dependency("nmap"):
        console.print("[red]Nmap is unavailable. Subnet scan cancelled.[/red]")
        return
    default = _subnet_from_settings()
    subnet = prompt_input(f"Subnet [{default}]: ").strip() or default
    run_process([resolve_command("nmap") or "nmap", "-sn", subnet], cancel_label="subnet scan")

def port_scan() -> None:
    if not ensure_dependency("nmap"):
        return
    target = prompt_input("Target IP/hostname: ").strip()
    if not target:
        return
    run_process([resolve_command("nmap") or "nmap", "-sV", target], cancel_label="port scan")

def os_fingerprint() -> None:
    if not ensure_dependency("nmap"):
        return
    target = prompt_input("Target IP/hostname: ").strip()
    if not target:
        return
    run_process([resolve_command("nmap") or "nmap", "-O", target], cancel_label="OS fingerprint")
