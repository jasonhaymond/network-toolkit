from rich.console import Console

from modules.connection_quality import connection_quality_test

console = Console()


def latency_monitor(config):
    console.print("[yellow]The old ICMP-only latency/jitter test has been replaced.[/yellow]")
    console.print("[cyan]Running Connection Quality Test instead.[/cyan]\n")
    return connection_quality_test(config)
