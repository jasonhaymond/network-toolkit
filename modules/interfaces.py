from __future__ import annotations
import socket
import psutil
from rich.console import Console
from rich.table import Table

console = Console()

def show_interfaces() -> None:
    table = Table(title="Network Interfaces")
    table.add_column("Interface")
    table.add_column("IPv4")
    table.add_column("Netmask")
    table.add_column("MAC")
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    for name, addresses in addrs.items():
        ipv4 = netmask = mac = ""
        for addr in addresses:
            if addr.family == socket.AF_INET:
                ipv4, netmask = addr.address, addr.netmask or ""
            elif getattr(psutil, "AF_LINK", None) == addr.family:
                mac = addr.address
        up = "up" if stats.get(name) and stats[name].isup else "down"
        table.add_row(f"{name} ({up})", ipv4, netmask, mac)
    console.print(table)
