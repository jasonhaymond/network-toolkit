"""
Shared utility helpers.

Anything that multiple modules need, like command execution, interface filtering,
and subnet calculation, belongs here. This keeps the diagnostics modules focused
instead of making them carry a backpack full of unrelated chores.
"""

import ipaddress
import platform
import re
import socket
import subprocess
from datetime import datetime
import psutil

UNHELPFUL_INTERFACE_PREFIXES = ("lo", "utun", "tun", "tap", "awdl", "llw", "ap", "bridge", "anpi")


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def run_command(command, timeout=30):
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return {"command": " ".join(command), "returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}
    except FileNotFoundError:
        return {"command": " ".join(command), "returncode": None, "stdout": "", "stderr": f"Command not found: {command[0]}"}
    except subprocess.TimeoutExpired:
        return {"command": " ".join(command), "returncode": None, "stdout": "", "stderr": "Command timed out"}


def netmask_to_cidr(netmask):
    try:
        return ipaddress.IPv4Network(f"0.0.0.0/{netmask}").prefixlen
    except Exception:
        return ""


def subnet_from_ip_netmask(ip, netmask):
    try:
        cidr = netmask_to_cidr(netmask)
        return str(ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False))
    except Exception:
        return ""


def is_unhelpful_interface(name, ip_address="", status=""):
    lower = name.lower()
    if lower.startswith(UNHELPFUL_INTERFACE_PREFIXES):
        return True
    if not ip_address:
        return True
    if status and status.lower() != "up":
        return True
    return False


def interface_records(include_unhelpful=False):
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    records = []
    for iface, addresses in addrs.items():
        ip = ""; netmask = ""; mac = ""
        for addr in addresses:
            if addr.family == socket.AF_INET:
                ip = addr.address; netmask = addr.netmask
            elif addr.family == psutil.AF_LINK:
                mac = addr.address
        status = "Up" if stats.get(iface) and stats[iface].isup else "Down"
        speed = f"{stats[iface].speed} Mbps" if iface in stats else "Unknown"
        unhelpful = is_unhelpful_interface(iface, ip, status)
        if unhelpful and not include_unhelpful:
            continue
        records.append({"interface": iface, "ip_address": ip, "netmask": netmask, "cidr": netmask_to_cidr(netmask) if netmask else "", "subnet": subnet_from_ip_netmask(ip, netmask) if ip and netmask else "", "mac": mac, "status": status, "speed": speed, "hidden_by_default": unhelpful})
    return records


def get_default_interface_name():
    system = platform.system()
    if system == "Darwin":
        result = run_command(["route", "-n", "get", "default"])
        match = re.search(r"interface:\s+(\S+)", result.get("stdout", ""))
        if match:
            return match.group(1)
    elif system == "Linux":
        result = run_command(["ip", "route", "show", "default"])
        match = re.search(r"\bdev\s+(\S+)", result.get("stdout", ""))
        if match:
            return match.group(1)
    return None


def get_primary_interface_record():
    default_iface = get_default_interface_name()
    records_all = interface_records(include_unhelpful=True)
    if default_iface:
        for record in records_all:
            if record["interface"] == default_iface and record.get("ip_address"):
                return record
    useful = interface_records(include_unhelpful=False)
    return useful[0] if useful else None


def get_dynamic_subnet():
    record = get_primary_interface_record()
    if record and record.get("subnet"):
        return record["subnet"]
    return None
