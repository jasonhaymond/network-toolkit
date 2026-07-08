from __future__ import annotations

import os
import platform
import shlex
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from core.config import load_settings
from core.dependencies import ensure_dependency, resolve_command
from core.interrupts import prompt_input, run_process, OperationCancelled

console = Console()

CAPTURE_DIR = Path("captures")
CAPTURE_DIR.mkdir(exist_ok=True)


def iperf_client() -> None:
    if not ensure_dependency("iperf3"):
        return
    server = prompt_input("iperf3 server IP/host: ").strip()
    if server:
        run_process([resolve_command("iperf3") or "iperf3", "-c", server], cancel_label="iperf3 client")


# ---------------------------------------------------------------------------
# Packet Capture Helpers
# ---------------------------------------------------------------------------


def _capture_backend() -> tuple[Optional[str], Optional[str]]:
    """
    Prefer tshark on Windows because tcpdump is normally not available there.
    Prefer tcpdump on macOS/Linux because it is simple and usually present.
    Returns (backend_name, command_path).
    """
    system = platform.system()

    if system == "Windows":
        if ensure_dependency("tshark"):
            return "tshark", resolve_command("tshark") or "tshark"
        return None, None

    if ensure_dependency("tcpdump"):
        return "tcpdump", resolve_command("tcpdump") or "tcpdump"

    if ensure_dependency("tshark"):
        return "tshark", resolve_command("tshark") or "tshark"

    return None, None


def _list_capture_interfaces(backend: str, command: str) -> None:
    console.print("\n[bold]Available capture interfaces[/bold]")
    console.print("[dim]Use the interface name or number shown by the capture tool.[/dim]\n")

    try:
        if backend == "tcpdump":
            run_process([command, "-D"], cancel_label="interface listing")
        else:
            run_process([command, "-D"], cancel_label="interface listing")
    except FileNotFoundError:
        console.print(f"[red]Could not run {command}.[/red]")


def _build_capture_filter() -> str:
    """
    Build a basic BPF capture filter that works with tcpdump and tshark -f.
    Keeping this simple prevents the usual disaster where a filter language eats
    the afternoon and half your will to live.
    """
    table = Table(title="Packet Capture Filter Options")
    table.add_column("Option")
    table.add_column("Example")
    table.add_row("Host/IP", "192.168.1.10")
    table.add_row("Network", "192.168.1.0/24")
    table.add_row("Port", "53, 443, 8000")
    table.add_row("Protocol", "tcp, udp, icmp, arp")
    table.add_row("Custom BPF", "host 192.168.1.10 and port 443")
    console.print(table)

    custom = Prompt.ask("Custom BPF filter, or leave blank to use guided fields", default="").strip()
    if custom:
        return custom

    host = Prompt.ask("Host/IP filter", default="").strip()
    network = Prompt.ask("Network filter", default="").strip()
    port = Prompt.ask("Port filter", default="").strip()
    proto = Prompt.ask("Protocol filter", default="").strip().lower()

    parts: list[str] = []

    if proto in {"tcp", "udp", "icmp", "arp"}:
        parts.append(proto)
    elif proto:
        console.print(f"[yellow]Ignoring unsupported protocol filter: {proto}[/yellow]")

    if host:
        parts.append(f"host {host}")

    if network:
        parts.append(f"net {network}")

    if port:
        if "," in port:
            ports = [p.strip() for p in port.split(",") if p.strip()]
            parts.append("(" + " or ".join(f"port {p}" for p in ports) + ")")
        else:
            parts.append(f"port {port}")

    return " and ".join(parts)


def _safe_filename(prefix: str = "capture", suffix: str = ".pcap") -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return CAPTURE_DIR / f"{prefix}-{stamp}{suffix}"


def _build_tcpdump_command(command: str, iface: str, bpf_filter: str, packet_count: str, duration: str, save_file: Optional[Path]) -> list[str]:
    cmd = [command, "-i", iface, "-nn", "-tttt"]

    if packet_count:
        cmd.extend(["-c", packet_count])

    # Line-buffer output when printing live so the display actually updates.
    if not save_file:
        cmd.append("-l")

    if save_file:
        cmd.extend(["-w", str(save_file)])

    if bpf_filter:
        cmd.extend(shlex.split(bpf_filter))

    return cmd


def _build_tshark_command(command: str, iface: str, bpf_filter: str, packet_count: str, duration: str, save_file: Optional[Path]) -> list[str]:
    cmd = [command, "-i", iface]

    if bpf_filter:
        cmd.extend(["-f", bpf_filter])

    if packet_count:
        cmd.extend(["-c", packet_count])

    if duration:
        cmd.extend(["-a", f"duration:{duration}"])

    if save_file:
        cmd.extend(["-w", str(save_file)])
    else:
        # Basic formatted live summary.
        cmd.extend([
            "-T", "fields",
            "-e", "frame.time",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "_ws.col.Protocol",
            "-e", "_ws.col.Info",
            "-E", "header=y",
            "-E", "separator= | ",
        ])

    return cmd


def _run_interruptible(command: list[str], duration: str = "") -> None:
    console.print("\n[green]Capture running.[/green] Press [bold]Ctrl+C[/bold] to stop and return to the toolkit.\n")
    console.print(f"[dim]{' '.join(shlex.quote(str(part)) for part in command)}[/dim]\n")

    start = time.time()
    process = None

    try:
        process = subprocess.Popen(command)

        while process.poll() is None:
            if duration and (time.time() - start) >= int(duration):
                console.print("\n[yellow]Capture duration reached. Stopping capture...[/yellow]")
                process.terminate()
                break
            time.sleep(0.25)

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping packet capture, not exiting toolkit...[/yellow]")
        if process and process.poll() is None:
            try:
                if os.name == "nt":
                    process.terminate()
                else:
                    process.send_signal(signal.SIGINT)
                process.wait(timeout=5)
            except Exception:
                process.kill()

    finally:
        if process and process.poll() is None:
            process.terminate()
        console.print("[green]Packet capture stopped.[/green]")


def packet_capture() -> None:
    """
    Interactive packet capture with:
    - Ctrl+C interrupt that returns to the toolkit
    - tcpdump/tshark backend support
    - guided BPF filters
    - packet-count limit
    - duration limit
    - optional pcap save
    - readable live output when not saving to file
    """
    console.print(Panel.fit("[bold cyan]Packet Capture[/bold cyan]", border_style="cyan"))

    backend, command = _capture_backend()
    if not backend or not command:
        console.print("[red]No supported capture backend is available.[/red]")
        return

    console.print(f"Using backend: [bold]{backend}[/bold]")

    if Confirm.ask("Show available capture interfaces first?", default=True):
        _list_capture_interfaces(backend, command)

    iface = Prompt.ask("Interface name/number to capture on").strip()
    if not iface:
        console.print("[yellow]No interface selected.[/yellow]")
        return

    bpf_filter = _build_capture_filter()

    packet_count = Prompt.ask("Packet count limit, blank for unlimited", default="").strip()
    if packet_count and not packet_count.isdigit():
        console.print("[yellow]Packet count must be a number. Ignoring.[/yellow]")
        packet_count = ""

    duration = Prompt.ask("Duration limit in seconds, blank for manual stop", default="").strip()
    if duration and not duration.isdigit():
        console.print("[yellow]Duration must be a number. Ignoring.[/yellow]")
        duration = ""

    save = Confirm.ask("Save to .pcap file instead of live readable output?", default=False)
    save_file = _safe_filename() if save else None

    if save_file:
        console.print(f"Saving capture to: [bold]{save_file}[/bold]")

    if backend == "tcpdump":
        cmd = _build_tcpdump_command(command, iface, bpf_filter, packet_count, duration, save_file)
    else:
        cmd = _build_tshark_command(command, iface, bpf_filter, packet_count, duration, save_file)

    _run_interruptible(cmd, duration=duration)

    if save_file and save_file.exists():
        console.print(f"[green]Saved:[/green] {save_file}")


# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------


def latency_monitor() -> None:
    target = load_settings().get("ping_target", "8.8.8.8")
    console.print("Press Ctrl+C to stop and return to the toolkit.")
    try:
        while True:
            run_process(["ping", "-n" if os.name == "nt" else "-c", "1", target], cancel_label="latency monitor")
            time.sleep(load_settings().get("monitoring_interval_seconds", 5))
    except OperationCancelled:
        console.print("[yellow]Latency monitor stopped.[/yellow]")
        return
