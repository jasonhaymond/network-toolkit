from rich.console import Console

from modules.connection_quality import connection_quality_submenu

console = Console()


def latency_monitor(config):
    console.print("[yellow]The old ICMP-only latency/jitter test has been replaced.[/yellow]")
    console.print("[cyan]Opening Connection Tests submenu instead.[/cyan]\n")
    return connection_quality_submenu(config)
