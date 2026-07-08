"""
Dependency detection and suggested/automatic fixes.

This module exists because "command not found" is a lazy error message.
If a tool is missing, we try to explain what it is, why it matters, and how to
install it on the current platform. If the user agrees, we can run the install
command automatically.

We do not auto-install silently. Surprise package installs are rude, and rude
software belongs in the same drawer as printer drivers.
"""

import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional
from rich.console import Console
from rich.prompt import Confirm
import socket
import ipaddress
import psutil
import shutil

console = Console()

def require_command(command_name: str) -> bool:
    return shutil.which(command_name) is not None


def get_dynamic_subnet() -> str:
    """
    Detect the first active IPv4 interface and return its subnet in CIDR format.
    Example: 192.168.1.0/24
    """

    interfaces = psutil.net_if_addrs()

    for interface_name, addresses in interfaces.items():
        for addr in addresses:
            if addr.family == socket.AF_INET:
                ip = addr.address
                netmask = addr.netmask

                if ip.startswith("127."):
                    continue

                if ip and netmask:
                    network = ipaddress.IPv4Network(
                        f"{ip}/{netmask}",
                        strict=False
                    )
                    return str(network)

    return "192.168.1.0/24"


@dataclass
class Dependency:
    command: str
    package_macos: Optional[str] = None
    package_apt: Optional[str] = None
    package_windows: Optional[str] = None
    description: str = ""
    windows_url: Optional[str] = None
    post_install_note: Optional[str] = None


DEPENDENCIES = {
    "nmap": Dependency(
        command="nmap",
        package_macos="nmap",
        package_apt="nmap",
        package_windows="Nmap",
        windows_url="https://nmap.org/download.html",
        description="Subnet scanning and port scanning.",
    ),
    "lldpctl": Dependency(
        command="lldpctl",
        package_macos="lldpd",
        package_apt="lldpd",
        package_windows=None,
        description="LLDP switch/port discovery.",
        post_install_note="Linux may need: sudo systemctl enable --now lldpd",
    ),
    "iperf3": Dependency(
        command="iperf3",
        package_macos="iperf3",
        package_apt="iperf3",
        package_windows="iPerf3",
        windows_url="https://iperf.fr/iperf-download.php",
        description="LAN/WAN throughput testing.",
    ),
    "speedtest-cli": Dependency(
        command="speedtest-cli",
        package_macos="speedtest-cli",
        package_apt="speedtest-cli",
        package_windows="Python package speedtest-cli",
        description="Internet speed testing.",
    ),
    "arp-scan": Dependency(
        command="arp-scan",
        package_macos="arp-scan",
        package_apt="arp-scan",
        package_windows=None,
        description="ARP-based subnet discovery.",
    ),
    "tcpdump": Dependency(
        command="tcpdump",
        package_macos=None,
        package_apt="tcpdump",
        package_windows=None,
        description="Packet capture.",
    ),
    "nmcli": Dependency(
        command="nmcli",
        package_macos=None,
        package_apt="network-manager",
        package_windows=None,
        description="Linux NetworkManager Wi-Fi and network diagnostics.",
    ),
    "iw": Dependency(
        command="iw",
        package_macos=None,
        package_apt="iw",
        package_windows=None,
        description="Linux Wi-Fi diagnostics.",
    ),
    "nslookup": Dependency(
        command="nslookup",
        package_macos=None,
        package_apt="dnsutils",
        package_windows=None,
        description="DNS lookup diagnostics.",
    ),
}


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def get_dependency(command: str) -> Dependency:
    return DEPENDENCIES.get(command, Dependency(command=command))


def platform_install_command(dep: Dependency):
    system = platform.system()

    if system == "Darwin" and dep.package_macos:
        if command_exists("brew"):
            return ["brew", "install", dep.package_macos], "Homebrew"
        return None, "Homebrew is not installed. Install Homebrew first: https://brew.sh"

    if system == "Linux" and dep.package_apt:
        if command_exists("apt"):
            return ["sudo", "apt", "install", "-y", dep.package_apt], "apt"
        return None, "This Linux installer currently supports apt-based distributions."

    if system == "Windows":
        if dep.windows_url:
            return None, f"Install {dep.package_windows or dep.command} manually from: {dep.windows_url}"
        return None, f"No automatic Windows installer is configured for {dep.command}."

    return None, f"No automatic install command is configured for {dep.command} on {system}."


def explain_missing(command: str):
    dep = get_dependency(command)
    console.print()
    console.print(f"[red]Missing command:[/red] {command}")

    if dep.description:
        console.print(f"[cyan]Used for:[/cyan] {dep.description}")

    install_cmd, note = platform_install_command(dep)

    if install_cmd:
        console.print(f"[green]Suggested fix:[/green] {' '.join(install_cmd)}")
    else:
        console.print(f"[yellow]Suggested fix:[/yellow] {note}")

    if dep.post_install_note:
        console.print(f"[yellow]Note:[/yellow] {dep.post_install_note}")

    return install_cmd


def offer_install(command: str) -> bool:
    """Offer to install a missing command.

    Returns True if the command exists after the attempt.
    """
    if command_exists(command):
        return True

    install_cmd = explain_missing(command)

    if not install_cmd:
        return False

    if not Confirm.ask("Attempt to install it now?", default=False):
        return False

    console.print()
    console.print(f"[cyan]Running:[/cyan] {' '.join(install_cmd)}")
    try:
        completed = subprocess.run(install_cmd)
    except Exception as e:
        console.print(f"[red]Install failed:[/red] {e}")
        return False

    if completed.returncode != 0:
        console.print("[red]Install command returned an error.[/red]")
        return False

    if command_exists(command):
        console.print(f"[green]{command} is now available.[/green]")
        return True

    console.print(f"[yellow]Install finished, but {command} still was not found in PATH.[/yellow]")
    console.print("[yellow]You may need to restart Terminal or update PATH.[/yellow]")
    return False


def require_command(command: str, auto_prompt: bool = True) -> bool:
    """Check whether command exists and optionally offer installation."""
    if command_exists(command):
        return True

    if auto_prompt:
        return offer_install(command)

    explain_missing(command)
    return False
