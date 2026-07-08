import platform
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.utils import run_command

console = Console()


def show_permissions_help():
    system = platform.system()

    console.print(Panel.fit(
        "[bold cyan]Network Toolkit Permissions Help[/bold cyan]\n"
        "Some network diagnostics require OS permissions or administrator rights.",
        border_style="cyan"
    ))

    if system == "Darwin":
        show_macos_permissions()
    elif system == "Windows":
        show_windows_permissions()
    elif system == "Linux":
        show_linux_permissions()
    else:
        console.print(f"[yellow]Unsupported/unknown platform: {system}[/yellow]")

    return {
        "platform": system,
        "topic": "permissions_help",
        "note": "Displayed platform-specific permissions and setup instructions.",
    }


def show_macos_permissions():
    table = Table(title="macOS Permissions / Settings")
    table.add_column("Need")
    table.add_column("Where / Command")
    table.add_column("Why")

    table.add_row(
        "Location Services",
        "System Settings → Privacy & Security → Location Services",
        "SSID, BSSID, and nearby AP info may be treated as location-sensitive data."
    )
    table.add_row(
        "Allow Terminal/iTerm/VS Code",
        "Location Services → enable your terminal app",
        "The app running Python needs permission, not just Python itself."
    )
    table.add_row(
        "Administrator Mode",
        "./launch.sh → option 2, or toolkit → Restart in Administrator Mode",
        "Needed for LLDP, packet capture, and some Wi-Fi diagnostics."
    )
    table.add_row(
        "Full Disk Access",
        "System Settings → Privacy & Security → Full Disk Access",
        "May help if logs, reports, or diagnostic files are blocked."
    )
    table.add_row(
        "Local Network",
        "System Settings → Privacy & Security → Local Network",
        "May be needed for discovery/scanning tools."
    )

    console.print(table)
    console.print("\n[bold]Recommended steps:[/bold]")
    console.print("1. Enable Location Services globally.")
    console.print("2. Enable Location Services for Terminal, iTerm2, or VS Code.")
    console.print("3. Quit and reopen the terminal app.")
    console.print("4. Run: [green]./launch.sh[/green]")
    console.print("5. Choose Administrator Mode for Wi-Fi AP scan, LLDP, or packet capture.")

    result = run_command(["defaults", "read", "/var/db/locationd/Library/Preferences/ByHost/com.apple.locationd", "LocationServicesEnabled"])
    if result.get("returncode") == 0:
        enabled = result.get("stdout", "").strip() == "1"
        console.print(f"\nGlobal Location Services best-effort check: [green]{enabled}[/green]")
    else:
        console.print("\n[yellow]Could not check global Location Services from CLI. This is common on newer macOS versions.[/yellow]")


def show_windows_permissions():
    table = Table(title="Windows 10+ Permissions / Setup")
    table.add_column("Need")
    table.add_column("Where / Command")
    table.add_column("Why")

    table.add_row(
        "Run as Administrator",
        "Right-click Terminal / PowerShell → Run as administrator",
        "Needed for detailed adapter info, route changes, packet capture, and some scans."
    )
    table.add_row(
        "Wi-Fi interface info",
        "netsh wlan show interfaces",
        "Built-in Windows Wi-Fi status and signal data."
    )
    table.add_row(
        "Wi-Fi AP scan",
        "netsh wlan show networks mode=bssid",
        "Shows SSIDs/BSSIDs visible to the adapter."
    )
    table.add_row(
        "Nmap",
        "Install from nmap.org",
        "Needed for subnet scans and port scans."
    )
    table.add_row(
        "Npcap",
        "Install with Nmap or from npcap.com",
        "Needed for packet capture and deeper discovery."
    )
    console.print(table)

    console.print("\n[bold]Recommended steps:[/bold]")
    console.print("1. Install Python 3 for Windows.")
    console.print("2. Install Nmap with Npcap.")
    console.print("3. Open Windows Terminal or PowerShell as Administrator.")
    console.print("4. Run: [green]launch.bat[/green] or [green]python main.py[/green]")


def show_linux_permissions():
    table = Table(title="Ubuntu/Linux Permissions / Setup")
    table.add_column("Need")
    table.add_column("Command")
    table.add_column("Why")

    table.add_row(
        "Network tools",
        "sudo apt install nmap lldpd wireless-tools iw net-tools iproute2 dnsutils iperf3",
        "Adds scanning, LLDP, Wi-Fi, DNS, and performance tools."
    )
    table.add_row(
        "Administrator Mode",
        "sudo .venv/bin/python main.py",
        "Needed for LLDP, Wi-Fi scanning, packet capture, and some scans."
    )
    table.add_row(
        "LLDP service",
        "sudo systemctl enable --now lldpd",
        "Allows switch/port neighbor discovery."
    )
    table.add_row(
        "Wi-Fi scan",
        "nmcli dev wifi list or sudo iw dev wlan0 scan",
        "Shows nearby APs when permissions and drivers allow it."
    )
    table.add_row(
        "Packet capture",
        "sudo apt install tcpdump",
        "Needed for packet capture."
    )
    console.print(table)

    console.print("\n[bold]Recommended steps:[/bold]")
    console.print("1. Install packages with apt.")
    console.print("2. Enable lldpd.")
    console.print("3. Run the toolkit normally for basic tests.")
    console.print("4. Use sudo for LLDP, Wi-Fi scan, and capture.")
