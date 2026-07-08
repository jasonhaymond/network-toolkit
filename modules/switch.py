from __future__ import annotations
import platform
from rich.console import Console
from core.dependencies import ensure_dependency, resolve_command
from core.utils import run_command
console = Console()

def switch_port_info() -> None:
    system = platform.system()
    if system in ("Darwin", "Linux"):
        if ensure_dependency("lldpctl"):
            code, out, err = run_command([resolve_command("lldpctl") or "lldpctl", "-f", "keyvalue"], timeout=15)
            console.print(out or err)
        else:
            console.print("[yellow]LLDP unavailable. Enable LLDP on switches and install lldpd/lldpctl.[/yellow]")
    else:
        console.print("Windows LLDP neighbor discovery is limited without vendor tools or Npcap/Wireshark.")
        console.print("This module will be expanded with PowerShell/Npcap parsing later.")

def poe_info() -> None:
    console.print("USB-C adapters usually cannot directly measure PoE.")
    console.print("PoE details normally come from LLDP negotiation or managed switch data.")
    switch_port_info()
