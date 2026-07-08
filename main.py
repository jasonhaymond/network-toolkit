from __future__ import annotations
from rich.console import Console
from rich.panel import Panel

from core.config import load_settings
from core.dependencies import startup_dependency_audit, print_dependency_status
from modules.interfaces import show_interfaces
from modules.scanning import subnet_scan, port_scan, os_fingerprint
from modules.internet import ping_test, public_ip, speed_test
from modules.dns import dns_test
from modules.wifi import wifi_info, wifi_scan
from modules.switch import switch_port_info, poe_info
from modules.advanced import iperf_client, packet_capture, latency_monitor
from modules.settings_menu import settings_menu

console = Console()

def pause() -> None:
    input("\nPress Enter to continue...")

def main() -> None:
    settings = load_settings()
    if settings.get("startup_dependency_audit", True):
        startup_dependency_audit(settings.get("auto_install_dependencies", "ask"))
        pause()
    while True:
        console.clear()
        console.print(Panel.fit("[bold cyan]Network Toolkit[/bold cyan]\nCross-platform diagnostics starter", border_style="cyan"))
        console.print("1) Interface / IP Info")
        console.print("2) DNS Test")
        console.print("3) Internet Ping Test")
        console.print("4) Public IP")
        console.print("5) Internet Speed Test")
        console.print("6) Wi-Fi Info")
        console.print("7) Wi-Fi AP Scan")
        console.print("8) Subnet Scan")
        console.print("9) Port Scan")
        console.print("10) OS Fingerprint")
        console.print("11) Switch + Port Info (LLDP)")
        console.print("12) PoE Info")
        console.print("13) LAN Speed Test (iperf3 client)")
        console.print("14) Packet Capture")
        console.print("15) Latency Monitor")
        console.print("16) Dependency Status")
        console.print("17) Settings")
        console.print("0) Exit")
        choice = input("\nSelection: ").strip()
        if choice == "1": show_interfaces()
        elif choice == "2": dns_test()
        elif choice == "3": ping_test()
        elif choice == "4": public_ip()
        elif choice == "5": speed_test()
        elif choice == "6": wifi_info()
        elif choice == "7": wifi_scan()
        elif choice == "8": subnet_scan()
        elif choice == "9": port_scan()
        elif choice == "10": os_fingerprint()
        elif choice == "11": switch_port_info()
        elif choice == "12": poe_info()
        elif choice == "13": iperf_client()
        elif choice == "14": packet_capture()
        elif choice == "15": latency_monitor()
        elif choice == "16": print_dependency_status()
        elif choice == "17": settings_menu()
        elif choice == "0": break
        else:
            console.print("[red]Invalid selection.[/red]")
        pause()

if __name__ == "__main__":
    main()
