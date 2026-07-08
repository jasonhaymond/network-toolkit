from __future__ import annotations
import subprocess
import requests
from rich.console import Console
from core.config import load_settings
console = Console()

def ping_test() -> None:
    target = load_settings().get("ping_target", "8.8.8.8")
    subprocess.run(["ping", "-n" if subprocess.os.name == "nt" else "-c", "4", target])

def public_ip() -> None:
    try:
        console.print(requests.get("https://api.ipify.org", timeout=5).text)
    except Exception as e:
        console.print(f"[red]Failed to get public IP:[/red] {e}")

def speed_test() -> None:
    try:
        import speedtest
        st = speedtest.Speedtest()
        st.get_best_server()
        down = st.download() / 1_000_000
        up = st.upload() / 1_000_000
        console.print(f"Download: {down:.2f} Mbps")
        console.print(f"Upload:   {up:.2f} Mbps")
    except Exception as e:
        console.print(f"[yellow]Speed test failed:[/yellow] {e}")
