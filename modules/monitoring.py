import time
from ping3 import ping
from rich.console import Console
from rich.prompt import IntPrompt

console = Console()


def latency_monitor(config):
    target = config["ping_target"]
    interval = int(config["monitoring_interval_seconds"])

    count = IntPrompt.ask(
        "How many samples? Use 0 for continuous",
        default=10,
    )

    console.print(f"[cyan]Latency / Jitter Monitor[/cyan]")
    console.print(f"Target: {target}")
    console.print("Press CTRL+C to stop if running continuous.\n")

    samples = []
    last_latency = None
    i = 0

    try:
        while count == 0 or i < count:
            i += 1
            result = ping(target, timeout=2)

            if result is None:
                console.print("[red]Packet lost[/red]")
                samples.append({
                    "sample": i,
                    "latency_ms": None,
                    "jitter_ms": None,
                    "lost": True,
                })
            else:
                latency_ms = round(result * 1000, 2)
                jitter = round(abs(latency_ms - last_latency), 2) if last_latency is not None else 0

                console.print(
                    f"Latency: [green]{latency_ms} ms[/green] | "
                    f"Jitter: [yellow]{jitter} ms[/yellow]"
                )

                samples.append({
                    "sample": i,
                    "latency_ms": latency_ms,
                    "jitter_ms": jitter,
                    "lost": False,
                })

                last_latency = latency_ms

            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\nStopped.")

    received = [s for s in samples if not s["lost"]]
    lost_count = len([s for s in samples if s["lost"]])

    summary = {
        "target": target,
        "sample_count": len(samples),
        "lost_count": lost_count,
        "packet_loss_percent": round((lost_count / len(samples)) * 100, 2) if samples else 0,
        "average_latency_ms": round(sum(s["latency_ms"] for s in received) / len(received), 2) if received else None,
        "average_jitter_ms": round(sum(s["jitter_ms"] for s in received) / len(received), 2) if received else None,
        "samples": samples,
    }

    return summary
