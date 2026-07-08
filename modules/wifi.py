"""
Wi-Fi diagnostics.

macOS, Windows, and Linux all expose Wi-Fi details differently, because one
standard interface would have been too merciful. This module hides that mess
behind a small set of functions used by the main menu.
"""

import os
import platform
import re
import shutil
from rich.console import Console
from rich.table import Table

from core.utils import run_command
from core.dependencies import require_command

console = Console()

AIRPORT_CANDIDATES = [
    "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
    "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/A/Resources/airport",
    "/usr/sbin/airport",
]


def find_airport():
    for path in AIRPORT_CANDIDATES:
        if os.path.exists(path):
            return path
    return shutil.which("airport")


def get_macos_wifi_device():
    result = run_command(["networksetup", "-listallhardwareports"])
    for block in result.get("stdout", "").split("\n\n"):
        if "Hardware Port: Wi-Fi" in block or "Hardware Port: AirPort" in block:
            match = re.search(r"Device:\s+(\S+)", block)
            if match:
                return match.group(1)
    return "en0"


def maybe_redact(value, show_sensitive=True):
    if show_sensitive:
        return value or ""
    if not value:
        return ""
    return "<hidden by toolkit privacy setting>"


def is_redacted(value):
    return value is not None and "<redacted>" in str(value).lower()


def privacy_guidance():
    return [
        "macOS may treat SSID/BSSID as location-sensitive data.",
        "Enable Location Services.",
        "Give Terminal, iTerm2, or VS Code Location Services permission.",
        "Quit and reopen the terminal app after changing permissions.",
        "Try Administrator Mode.",
    ]


def check_location_services_status():
    result = run_command(["defaults", "read", "/var/db/locationd/Library/Preferences/ByHost/com.apple.locationd", "LocationServicesEnabled"])
    enabled = None
    if result.get("returncode") == 0:
        enabled = result.get("stdout", "").strip() == "1"
    return {
        "collector": "defaults locationd",
        "location_services_enabled": enabled,
        "raw": result,
        "note": "Best-effort global check only. Per-app terminal permission must be checked in System Settings.",
    }


def get_corewlan_info(show_sensitive=True):
    try:
        from CoreWLAN import CWInterface
    except Exception as e:
        return {"available": False, "error": f"CoreWLAN unavailable: {e}"}

    try:
        iface = CWInterface.interface()
        if iface is None:
            return {"available": True, "connected": False, "error": "No Wi-Fi interface."}

        ssid = iface.ssid()
        bssid = iface.bssid()
        return {
            "available": True,
            "collector": "CoreWLAN",
            "interface_name": str(iface.interfaceName() or ""),
            "connected": bool(ssid or bssid),
            "ssid": maybe_redact(str(ssid or ""), show_sensitive),
            "bssid": maybe_redact(str(bssid or ""), show_sensitive),
            "rssi": iface.rssiValue(),
            "noise": iface.noiseMeasurement(),
            "channel": str(iface.wlanChannel() or ""),
            "transmit_rate": iface.transmitRate(),
            "security": str(iface.security() or ""),
            "phy_mode": str(iface.activePHYMode() or ""),
            "country_code": str(iface.countryCode() or ""),
            "redacted_by_macos": is_redacted(ssid) or is_redacted(bssid),
        }
    except Exception as e:
        return {"available": True, "error": f"CoreWLAN collection failed: {e}"}


def scan_corewlan_networks(show_sensitive=True):
    try:
        from CoreWLAN import CWInterface
    except Exception as e:
        return {"available": False, "error": f"CoreWLAN unavailable: {e}", "networks": []}

    try:
        iface = CWInterface.interface()
        if iface is None:
            return {"available": True, "error": "No Wi-Fi interface.", "networks": []}

        networks, error = iface.scanForNetworksWithName_error_(None, None)
        results = []
        if networks:
            for network in networks:
                ssid = network.ssid()
                bssid = network.bssid()
                results.append({
                    "ssid": maybe_redact(str(ssid or ""), show_sensitive),
                    "bssid": maybe_redact(str(bssid or ""), show_sensitive),
                    "rssi": network.rssiValue(),
                    "noise": network.noiseMeasurement(),
                    "channel": str(network.wlanChannel() or ""),
                    "security": str(network.security() or ""),
                    "phy_mode": str(network.phyMode() or ""),
                    "redacted_by_macos": is_redacted(ssid) or is_redacted(bssid),
                })
        return {"available": True, "collector": "CoreWLAN scanForNetworks", "networks": results, "count": len(results), "error": str(error) if error else ""}
    except Exception as e:
        return {"available": True, "collector": "CoreWLAN scanForNetworks", "error": f"CoreWLAN scan failed: {e}", "networks": [], "count": 0}


def parse_system_profiler_wifi(output, show_sensitive=True):
    data = {
        "current_network": "",
        "bssid": "",
        "channel": "",
        "signal_noise": "",
        "security": "",
        "country_code": "",
        "raw_output": output,
        "redacted_by_macos": "<redacted>" in output.lower(),
    }
    current_match = re.search(r"Current Network Information:\s*\n\s*(.*?):", output)
    if current_match:
        data["current_network"] = maybe_redact(current_match.group(1).strip(), show_sensitive)
    for field, regex in [
        ("bssid", r"BSSID:\s*(.*)"),
        ("channel", r"Channel:\s*(.*)"),
        ("signal_noise", r"Signal / Noise:\s*(.*)"),
        ("security", r"Security:\s*(.*)"),
        ("country_code", r"Country Code:\s*(.*)"),
    ]:
        match = re.search(regex, output)
        if match:
            data[field] = match.group(1).strip()
    return data


def get_preferred_networks(device):
    result = run_command(["networksetup", "-listpreferredwirelessnetworks", device])
    networks = []
    for line in result.get("stdout", "").splitlines():
        line = line.strip()
        if line and not line.startswith("Preferred networks"):
            networks.append(line)
    return {"collector": "networksetup preferred networks", "device": device, "preferred_networks": networks, "raw": result}


def parse_windows_wifi_interfaces(output):
    data = {}
    mapping = {
        "Name": "interface_name",
        "Description": "description",
        "GUID": "guid",
        "Physical address": "bssid_or_adapter_mac",
        "State": "state",
        "SSID": "ssid",
        "BSSID": "bssid",
        "Network type": "network_type",
        "Radio type": "radio_type",
        "Authentication": "security",
        "Channel": "channel",
        "Receive rate (Mbps)": "receive_rate_mbps",
        "Transmit rate (Mbps)": "transmit_rate_mbps",
        "Signal": "signal",
    }
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        if key in mapping:
            data[mapping[key]] = value
    return data


def parse_nmcli_wifi(output):
    networks = []
    for line in output.splitlines():
        parts = line.split(":")
        if len(parts) >= 7:
            networks.append({
                "active": parts[0],
                "ssid": parts[1],
                "bssid": ":".join(parts[2:8]) if len(parts) > 8 else parts[2],
                "channel": parts[-4] if len(parts) >= 4 else "",
                "rate": parts[-3] if len(parts) >= 3 else "",
                "signal": parts[-2] if len(parts) >= 2 else "",
                "security": parts[-1],
            })
    return networks


def print_wifi_summary(summary):
    table = Table(title="Wi-Fi Summary")
    table.add_column("Item")
    table.add_column("Result")
    for label, key in [
        ("Collector", "collector"),
        ("Interface", "interface_name"),
        ("SSID", "ssid"),
        ("BSSID", "bssid"),
        ("RSSI/Signal", "rssi"),
        ("Noise", "noise"),
        ("Channel", "channel"),
        ("TX Rate", "transmit_rate"),
        ("RX Rate", "receive_rate"),
        ("Security", "security"),
        ("PHY/Radio", "phy_mode"),
        ("Country", "country_code"),
    ]:
        table.add_row(label, str(summary.get(key, "")))
    console.print(table)


def wifi_info(config=None):
    system = platform.system()
    show_sensitive = True if config is None else bool(config.get("show_sensitive_wifi_identifiers", True))
    console.print("[cyan]Wi-Fi Information[/cyan]\n")

    if system == "Darwin":
        device = get_macos_wifi_device()
        location = check_location_services_status()
        core = get_corewlan_info(show_sensitive)
        profiler = run_command(["system_profiler", "SPAirPortDataType"], timeout=60)
        profiler_data = parse_system_profiler_wifi(profiler.get("stdout", ""), show_sensitive)
        preferred = get_preferred_networks(device)

        summary = {
            "collector": "CoreWLAN + system_profiler + networksetup",
            "interface_name": core.get("interface_name") or device,
            "ssid": core.get("ssid") or profiler_data.get("current_network"),
            "bssid": core.get("bssid") or profiler_data.get("bssid"),
            "rssi": core.get("rssi", ""),
            "noise": core.get("noise", ""),
            "channel": core.get("channel") or profiler_data.get("channel"),
            "transmit_rate": core.get("transmit_rate", ""),
            "receive_rate": "",
            "security": core.get("security") or profiler_data.get("security"),
            "phy_mode": core.get("phy_mode", ""),
            "country_code": core.get("country_code") or profiler_data.get("country_code"),
            "redacted_by_macos": bool(core.get("redacted_by_macos") or profiler_data.get("redacted_by_macos")),
        }
        print_wifi_summary(summary)

        warnings = []
        if summary["redacted_by_macos"]:
            warnings.extend(privacy_guidance())
        if location.get("location_services_enabled") is False:
            warnings.append("Global Location Services appears to be OFF.")
        if warnings:
            console.print("\n[yellow]Wi-Fi Permission Notes[/yellow]")
            for item in warnings:
                console.print(f"- {item}")

        return {"collector": summary["collector"], "summary": summary, "corewlan": core, "location_services": location, "system_profiler": profiler_data, "preferred_networks": preferred, "guidance": warnings}

    if system == "Windows":
        result = run_command(["netsh", "wlan", "show", "interfaces"])
        parsed = parse_windows_wifi_interfaces(result.get("stdout", ""))
        summary = {
            "collector": "netsh wlan",
            "interface_name": parsed.get("interface_name", ""),
            "ssid": parsed.get("ssid", ""),
            "bssid": parsed.get("bssid", ""),
            "rssi": parsed.get("signal", ""),
            "noise": "",
            "channel": parsed.get("channel", ""),
            "transmit_rate": parsed.get("transmit_rate_mbps", ""),
            "receive_rate": parsed.get("receive_rate_mbps", ""),
            "security": parsed.get("security", ""),
            "phy_mode": parsed.get("radio_type", ""),
            "country_code": "",
        }
        print_wifi_summary(summary)
        return {"collector": "netsh wlan", "summary": summary, "parsed": parsed, "raw": result}

    if system == "Linux":
        if not require_command("nmcli"):
            return {
                "collector": "nmcli",
                "success": False,
                "error": "nmcli is required for Linux Wi-Fi diagnostics and is not installed.",
                "missing_command": "nmcli",
            }

        result = run_command(["nmcli", "-t", "-f", "active,ssid,bssid,chan,rate,signal,security", "dev", "wifi"], timeout=30)
        networks = parse_nmcli_wifi(result.get("stdout", ""))
        active = next((n for n in networks if n.get("active") == "yes"), networks[0] if networks else {})
        summary = {
            "collector": "nmcli",
            "interface_name": "",
            "ssid": active.get("ssid", ""),
            "bssid": active.get("bssid", ""),
            "rssi": active.get("signal", ""),
            "noise": "",
            "channel": active.get("channel", ""),
            "transmit_rate": active.get("rate", ""),
            "receive_rate": "",
            "security": active.get("security", ""),
            "phy_mode": "",
            "country_code": "",
        }
        print_wifi_summary(summary)
        return {"collector": "nmcli", "summary": summary, "networks": networks, "raw": result}

    return {"error": f"Unsupported platform: {system}"}


def wifi_scan(config=None):
    system = platform.system()
    show_sensitive = True if config is None else bool(config.get("show_sensitive_wifi_identifiers", True))
    console.print("[cyan]Wi-Fi AP Scan[/cyan]\n")

    if system == "Darwin":
        core_scan = scan_corewlan_networks(show_sensitive)
        networks = core_scan.get("networks", [])
    elif system == "Windows":
        result = run_command(["netsh", "wlan", "show", "networks", "mode=bssid"], timeout=60)
        console.print(result["stdout"] or result["stderr"])
        return result
    elif system == "Linux":
        if not require_command("nmcli"):
            return {
                "collector": "nmcli",
                "success": False,
                "error": "nmcli is required for Linux Wi-Fi scanning and is not installed.",
                "missing_command": "nmcli",
            }

        result = run_command(["nmcli", "-t", "-f", "active,ssid,bssid,chan,rate,signal,security", "dev", "wifi", "list"], timeout=60)
        networks = parse_nmcli_wifi(result.get("stdout", ""))
        if not networks:
            console.print(result["stdout"] or result["stderr"])
            return result
    else:
        return {"error": f"Unsupported platform: {system}"}

    if networks:
        table = Table(title="Wi-Fi AP Scan")
        table.add_column("SSID")
        table.add_column("BSSID")
        table.add_column("Signal/RSSI")
        table.add_column("Noise")
        table.add_column("Channel")
        table.add_column("Rate")
        table.add_column("Security")
        table.add_column("PHY")
        for n in sorted(networks, key=lambda x: str(x.get("rssi") or x.get("signal") or ""), reverse=True):
            table.add_row(
                str(n.get("ssid", "")),
                str(n.get("bssid", "")),
                str(n.get("rssi", n.get("signal", ""))),
                str(n.get("noise", "")),
                str(n.get("channel", "")),
                str(n.get("rate", "")),
                str(n.get("security", "")),
                str(n.get("phy_mode", "")),
            )
        console.print(table)
        return {"collector": "platform wifi scan", "networks": networks, "count": len(networks)}

    message = "Wi-Fi scan returned no networks. Check permissions, adapter state, and OS restrictions."
    console.print(f"[yellow]{message}[/yellow]")
    return {"collector": "platform wifi scan", "networks": [], "count": 0, "guidance": privacy_guidance() if system == "Darwin" else []}


def advanced_wifi_diagnostics(config=None):
    system = platform.system()
    show_sensitive = True if config is None else bool(config.get("show_sensitive_wifi_identifiers", True))
    console.print("[cyan]Advanced Wi-Fi Diagnostics[/cyan]\n")

    if system == "Darwin":
        device = get_macos_wifi_device()
        core = get_corewlan_info(show_sensitive)
        scan = scan_corewlan_networks(show_sensitive)
        location = check_location_services_status()
        preferred = get_preferred_networks(device)
        checks = []
        for command in [["wdutil", "info"], ["sudo", "wdutil", "info"], ["wdutil", "dump"], ["sudo", "wdutil", "dump"]]:
            result = run_command(command, timeout=60)
            stdout = result.get("stdout", "")
            checks.append({
                "command": result["command"],
                "returncode": result["returncode"],
                "useful": bool(stdout and "usage: sudo wdutil" not in stdout.lower()),
                "redacted_by_macos": "<redacted>" in stdout.lower(),
                "stdout": stdout,
                "stderr": result.get("stderr", ""),
            })
        warnings = []
        if core.get("redacted_by_macos") or any(c.get("redacted_by_macos") for c in checks):
            warnings.extend(privacy_guidance())
        if location.get("location_services_enabled") is False:
            warnings.append("Global Location Services appears to be OFF.")
        if warnings:
            console.print("[yellow]Recommended macOS Settings[/yellow]")
            for item in warnings:
                console.print(f"- {item}")
        return {"collector": "advanced macOS Wi-Fi diagnostics", "corewlan": core, "corewlan_scan": scan, "location_services": location, "preferred_networks": preferred, "wdutil_checks": checks, "guidance": warnings}

    if system == "Windows":
        results = {
            "interfaces": run_command(["netsh", "wlan", "show", "interfaces"]),
            "drivers": run_command(["netsh", "wlan", "show", "drivers"]),
            "networks": run_command(["netsh", "wlan", "show", "networks", "mode=bssid"]),
        }
        for name, result in results.items():
            console.print(f"\n[cyan]{name}[/cyan]")
            console.print(result["stdout"] or result["stderr"])
        return {"collector": "Windows netsh advanced Wi-Fi diagnostics", "results": results}

    if system == "Linux":
        commands = {
            "nmcli_device": ["nmcli", "device", "status"],
            "nmcli_wifi": ["nmcli", "dev", "wifi", "list"],
            "iw_dev": ["iw", "dev"],
            "rfkill": ["rfkill", "list"],
        }
        results = {name: run_command(cmd, timeout=60) for name, cmd in commands.items()}
        for name, result in results.items():
            console.print(f"\n[cyan]{name}[/cyan]")
            console.print(result["stdout"] or result["stderr"])
        return {"collector": "Linux advanced Wi-Fi diagnostics", "results": results}

    return {"error": f"Unsupported platform: {system}"}
