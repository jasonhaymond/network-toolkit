from __future__ import annotations
import subprocess, time
from rich.console import Console
from core.config import load_settings
from core.dependencies import ensure_dependency
console = Console()

def iperf_client() -> None:
    if not ensure_dependency("iperf3"):
        return
    server = input("iperf3 server IP/host: ").strip()
    if server:
        subprocess.run(["iperf3", "-c", server])

def packet_capture() -> None:
    if not ensure_dependency("tcpdump"):
        return
    iface = input("Interface name: ").strip()
    if iface:
        subprocess.run(["tcpdump", "-i", iface])

def latency_monitor() -> None:
    target = load_settings().get("ping_target", "8.8.8.8")
    console.print("Press Ctrl+C to stop.")
    try:
        while True:
            subprocess.run(["ping", "-n" if subprocess.os.name == "nt" else "-c", "1", target])
            time.sleep(load_settings().get("monitoring_interval_seconds", 5))
    except KeyboardInterrupt:
        console.print("Stopped.")
