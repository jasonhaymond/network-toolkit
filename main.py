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
from core.interrupts import OperationCancelled, prompt_input, run_menu_action, cancel_message

console = Console()

def pause() -> None:
    try:
        prompt_input("\nPress Enter to continue...")
    except OperationCancelled:
        cancel_message()


def main() -> None:
    settings = load_settings()
    if settings.get("startup_dependency_audit", True):
        try:
            startup_dependency_audit(settings.get("auto_install_dependencies", "ask"))
        except OperationCancelled:
            cancel_message("Dependency audit cancelled. Continuing to menu.")
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
        try:
            choice = prompt_input("\nSelection: ").strip()
        except OperationCancelled:
            console.print("\n[yellow]Use 0 to exit.[/yellow]")
            continue
        cancelled = False
        if choice == "1": cancelled = run_menu_action(show_interfaces)
        elif choice == "2": cancelled = run_menu_action(dns_test)
        elif choice == "3": cancelled = run_menu_action(ping_test)
        elif choice == "4": cancelled = run_menu_action(public_ip)
        elif choice == "5": cancelled = run_menu_action(speed_test)
        elif choice == "6": cancelled = run_menu_action(wifi_info)
        elif choice == "7": cancelled = run_menu_action(wifi_scan)
        elif choice == "8": cancelled = run_menu_action(subnet_scan)
        elif choice == "9": cancelled = run_menu_action(port_scan)
        elif choice == "10": cancelled = run_menu_action(os_fingerprint)
        elif choice == "11": cancelled = run_menu_action(switch_port_info)
        elif choice == "12": cancelled = run_menu_action(poe_info)
        elif choice == "13": cancelled = run_menu_action(iperf_client)
        elif choice == "14": cancelled = run_menu_action(packet_capture)
        elif choice == "15": cancelled = run_menu_action(latency_monitor)
        elif choice == "16": cancelled = run_menu_action(print_dependency_status)
        elif choice == "17": cancelled = run_menu_action(settings_menu)
        elif choice == "0": break
        else:
            console.print("[red]Invalid selection.[/red]")
        if not cancelled:
            pause()

if __name__ == "__main__":
    main()
