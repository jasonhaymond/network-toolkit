from __future__ import annotations
import socket, time
from rich.console import Console
from core.config import load_settings
console = Console()

def dns_test() -> None:
    settings = load_settings()
    domain = settings.get("dns_test_domain", "google.com")
    start = time.perf_counter()
    try:
        ips = socket.gethostbyname_ex(domain)[2]
        elapsed = (time.perf_counter() - start) * 1000
        console.print(f"Domain: {domain}")
        console.print(f"Resolved: {', '.join(ips)}")
        console.print(f"Latency: {elapsed:.1f} ms")
    except Exception as e:
        console.print(f"[red]DNS test failed:[/red] {e}")
