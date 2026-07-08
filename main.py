import atexit
import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt

from core.config import load_config, settings_menu
from core.exports import ReportSession

from modules.interfaces import show_interfaces, show_all_interfaces
from modules.gateway import show_gateway
from modules.dns import dns_test
from modules.internet import internet_test, speed_test
from modules.wifi import wifi_info, wifi_scan, advanced_wifi_diagnostics
from modules.scanning import subnet_scan
from modules.monitoring import latency_monitor
from modules.connection_quality import connection_quality_test
from modules.switch import switch_port_info
from modules.permissions import show_permissions_help

console = Console()


def goodbye():
    pass


atexit.register(goodbye)


def clean_exit():
    console.print()
    console.print("[green]Network Toolkit exited successfully.[/green]")
    console.print()
    sys.exit(0)


def is_admin():
    if hasattr(os, "geteuid"):
        return os.geteuid() == 0
    return False


def restart_in_admin_mode():
    if is_admin():
        console.print("[green]Already running in Administrator Mode.[/green]")
        Prompt.ask("Press Enter to continue")
        return

    console.print()
    console.print("[yellow]Administrator Mode is useful for Wi-Fi diagnostics, LLDP, packet capture, and deeper scans.[/yellow]")

    if not Confirm.ask("Restart Network Toolkit in Administrator Mode now?", default=True):
        return

    python_path = sys.executable
    main_path = Path(__file__).resolve()

    console.print()
    console.print("[cyan]Restarting with sudo...[/cyan]")
    console.print()

    try:
        subprocess.run(["sudo", python_path, str(main_path)])
    except KeyboardInterrupt:
        pass

    clean_exit()


def run_admin_required(report, name, func, *args):
    if not is_admin():
        console.print()
        console.print("[yellow]This tool may require Administrator Mode for complete results.[/yellow]")
        if Confirm.ask("Restart in Administrator Mode now?", default=True):
            restart_in_admin_mode()
            return

    run_and_collect(report, name, func, *args)


def run_and_collect(report, name, func, *args):
    result = func(*args)
    if result is not None:
        report.add_result(name, result)
    Prompt.ask("Press Enter to continue")


def export_menu(report, config):
    while True:
        console.clear()
        table = Table(title="Export Reports")
        table.add_column("#")
        table.add_column("Export Type")
        table.add_row("1", "Export JSON")
        table.add_row("2", "Export CSV")
        table.add_row("3", "Export HTML")
        table.add_row("4", "Export All")
        table.add_row("0", "Return")
        console.print(table)

        choice = Prompt.ask("Selection")

        if choice == "1":
            console.print(report.export_json(config))
        elif choice == "2":
            console.print(report.export_csv(config))
        elif choice == "3":
            console.print(report.export_html(config))
        elif choice == "4":
            console.print(report.export_all(config))
        elif choice == "0":
            return

        Prompt.ask("Press Enter to continue")


def main_menu():
    config = load_config()
    report = ReportSession()

    while True:
        console.clear()

        mode = "Administrator" if is_admin() else "Normal"

        table = Table(title=f"Network Toolkit — {mode} Mode")
        table.add_column("#")
        table.add_column("Test / Tool")

        options = [
            "Useful Interface / IP Info",
            "All Interface / IP Info",
            "Gateway Info",
            "DNS Test",
            "Internet Reachability",
            "Internet Speed Test",
            "Wi-Fi Info",
            "Wi-Fi AP Scan",
            "Advanced Wi-Fi Diagnostics",
            "Subnet Scan",
            "Switch + Port Info",
            "Connection Quality Test",
            "Restart in Administrator Mode",
            "Permissions / Setup Help",
            "Export Reports",
            "Settings"
        ]

        for i, item in enumerate(options, start=1):
            table.add_row(str(i), item)
        
        table.add_row("", "")
        table.add_row("0", "Exit")

        console.print(table)
        console.print(f"Collected report sections: [green]{len(report.results)}[/green]")
        console.print(f"Current mode: [cyan]{mode}[/cyan]")

        choice = Prompt.ask("Selection")

        if choice == "1":
            run_and_collect(report, "useful_interface_ip_info", show_interfaces)
        elif choice == "2":
            run_and_collect(report, "all_interface_ip_info", show_all_interfaces)
        elif choice == "3":
            run_and_collect(report, "gateway_info", show_gateway)
        elif choice == "4":
            run_and_collect(report, "dns_test", dns_test, config)
        elif choice == "5":
            run_and_collect(report, "internet_reachability", internet_test, config)
        elif choice == "6":
            run_and_collect(report, "internet_speed_test", speed_test)
        elif choice == "7":
            run_and_collect(report, "wifi_info", wifi_info, config)
        elif choice == "8":
            run_admin_required(report, "wifi_ap_scan", wifi_scan, config)
        elif choice == "9":
            run_admin_required(report, "advanced_wifi_diagnostics", advanced_wifi_diagnostics, config)
        elif choice == "10":
            run_and_collect(report, "subnet_scan", subnet_scan, config)
        elif choice == "11":
            run_admin_required(report, "switch_port_info", switch_port_info)
        elif choice == "12":
            run_and_collect(report, "connection_quality_test", connection_quality_test, config)
        elif choice == "13":
            restart_in_admin_mode()
        elif choice == "14":
            run_and_collect(report, "permissions_help", show_permissions_help)
        elif choice == "15":
            export_menu(report, config)
        elif choice == "16":
            settings_menu()
            config = load_config()
        elif choice == "0":
            clean_exit()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Interrupted by user.[/yellow]")
        console.print()
        sys.exit(0)
    except Exception as e:
        console.print()
        console.print(f"[red]Unexpected error:[/red] {e}")
        console.print()
        sys.exit(1)
