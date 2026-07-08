from __future__ import annotations
import platform
from rich.console import Console
from core.utils import run_command
console = Console()

def wifi_info() -> None:
    system = platform.system()
    if system == "Windows":
        code, out, err = run_command(["netsh", "wlan", "show", "interfaces"])
    elif system == "Darwin":
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        code, out, err = run_command([airport, "-I"])
    else:
        code, out, err = run_command(["nmcli", "dev", "wifi"])
    console.print(out or err or "No Wi-Fi info available.")

def wifi_scan() -> None:
    system = platform.system()
    if system == "Windows":
        code, out, err = run_command(["netsh", "wlan", "show", "networks", "mode=bssid"])
    elif system == "Darwin":
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        code, out, err = run_command([airport, "-s"])
    else:
        code, out, err = run_command(["nmcli", "dev", "wifi", "list"])
    console.print(out or err or "No Wi-Fi scan available.")
