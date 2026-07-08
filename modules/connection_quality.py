import socket
import ssl
import statistics
import subprocess
import time
from urllib.parse import urlparse

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.utils import run_command

console = Console()


def _safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default):
    try:
        return float(value)
    except Exception:
        return default


def summarize_samples(samples):
    good = [s for s in samples if s.get("success") and s.get("latency_ms") is not None]
    failed = [s for s in samples if not s.get("success")]
    latencies = [s["latency_ms"] for s in good]

    if not latencies:
        return {
            "success": False,
            "attempts": len(samples),
            "successful_attempts": 0,
            "failed_attempts": len(failed),
            "loss_percent": 100.0 if samples else None,
            "min_ms": None,
            "avg_ms": None,
            "max_ms": None,
            "jitter_ms": None,
            "samples": samples,
        }

    jitter = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    return {
        "success": True,
        "attempts": len(samples),
        "successful_attempts": len(good),
        "failed_attempts": len(failed),
        "loss_percent": round((len(failed) / len(samples)) * 100, 2) if samples else 0,
        "min_ms": round(min(latencies), 2),
        "avg_ms": round(sum(latencies) / len(latencies), 2),
        "max_ms": round(max(latencies), 2),
        "jitter_ms": round(jitter, 2),
        "samples": samples,
    }


def tcp_connect_test(host, port, attempts=10, timeout=3):
    samples = []

    for i in range(1, attempts + 1):
        start = time.perf_counter()
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            latency = (time.perf_counter() - start) * 1000
            sock.close()
            samples.append({"sample": i, "success": True, "latency_ms": round(latency, 2), "error": ""})
        except Exception as e:
            samples.append({"sample": i, "success": False, "latency_ms": None, "error": str(e)})

    result = summarize_samples(samples)
    result.update({
        "method": "TCP Connect",
        "target": f"{host}:{port}",
        "notes": "Measures TCP connection establishment time. Useful when ICMP ping is blocked.",
    })
    return result


def dns_latency_test(domain, dns_server=None, attempts=10, timeout=3):
    samples = []

    for i in range(1, attempts + 1):
        start = time.perf_counter()
        try:
            if dns_server:
                completed = subprocess.run(
                    ["nslookup", domain, dns_server],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if completed.returncode != 0:
                    raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
            else:
                socket.getaddrinfo(domain, None)

            latency = (time.perf_counter() - start) * 1000
            samples.append({"sample": i, "success": True, "latency_ms": round(latency, 2), "error": ""})
        except Exception as e:
            samples.append({"sample": i, "success": False, "latency_ms": None, "error": str(e)})

    target = f"{domain} via {dns_server}" if dns_server else domain
    result = summarize_samples(samples)
    result.update({
        "method": "DNS Lookup",
        "target": target,
        "notes": "Measures DNS resolution time. Very useful on corporate networks.",
    })
    return result


def https_request_test(url, attempts=10, timeout=3):
    samples = []
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"

    if parsed.query:
        path += "?" + parsed.query

    for i in range(1, attempts + 1):
        try:
            timings = {}
            overall_start = time.perf_counter()

            dns_start = time.perf_counter()
            addr_info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            timings["dns_ms"] = round((time.perf_counter() - dns_start) * 1000, 2)

            address = addr_info[0][4]

            tcp_start = time.perf_counter()
            raw_sock = socket.create_connection(address, timeout=timeout)
            timings["tcp_ms"] = round((time.perf_counter() - tcp_start) * 1000, 2)

            sock = raw_sock
            if parsed.scheme == "https":
                tls_start = time.perf_counter()
                context = ssl.create_default_context()
                sock = context.wrap_socket(raw_sock, server_hostname=host)
                timings["tls_ms"] = round((time.perf_counter() - tls_start) * 1000, 2)
            else:
                timings["tls_ms"] = 0

            request = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                "User-Agent: network-toolkit\r\n"
                "Connection: close\r\n\r\n"
            ).encode("utf-8")

            first_byte_start = time.perf_counter()
            sock.sendall(request)
            first = sock.recv(1)
            timings["first_byte_ms"] = round((time.perf_counter() - first_byte_start) * 1000, 2)

            total_bytes = len(first)
            while total_bytes < 4096:
                chunk = sock.recv(4096 - total_bytes)
                if not chunk:
                    break
                total_bytes += len(chunk)

            sock.close()
            total_ms = round((time.perf_counter() - overall_start) * 1000, 2)

            samples.append({
                "sample": i,
                "success": True,
                "latency_ms": total_ms,
                "dns_ms": timings["dns_ms"],
                "tcp_ms": timings["tcp_ms"],
                "tls_ms": timings["tls_ms"],
                "first_byte_ms": timings["first_byte_ms"],
                "bytes_read": total_bytes,
                "error": "",
            })

        except Exception as e:
            samples.append({"sample": i, "success": False, "latency_ms": None, "error": str(e)})

    result = summarize_samples(samples)
    result.update({
        "method": "HTTPS Request",
        "target": url,
        "notes": "Measures application-like latency: DNS, TCP, TLS, first byte, and total response.",
    })

    good = [s for s in samples if s.get("success")]
    if good:
        for key in ["dns_ms", "tcp_ms", "tls_ms", "first_byte_ms"]:
            values = [s[key] for s in good if key in s and s[key] is not None]
            result[f"avg_{key}"] = round(sum(values) / len(values), 2) if values else None

    return result


def icmp_test(target, attempts=10, timeout=3):
    try:
        from ping3 import ping
        samples = []
        for i in range(1, attempts + 1):
            try:
                result = ping(target, timeout=timeout)
                if result is None:
                    samples.append({"sample": i, "success": False, "latency_ms": None, "error": "timeout/blocked"})
                else:
                    samples.append({"sample": i, "success": True, "latency_ms": round(result * 1000, 2), "error": ""})
            except Exception as e:
                samples.append({"sample": i, "success": False, "latency_ms": None, "error": str(e)})

        result = summarize_samples(samples)
        result.update({
            "method": "ICMP Ping",
            "target": target,
            "notes": "Traditional ping. Often blocked or rate-limited on corporate networks.",
        })
        return result
    except Exception as e:
        return {
            "method": "ICMP Ping",
            "target": target,
            "success": False,
            "error": f"ICMP test unavailable: {e}",
            "notes": "Traditional ping. Often blocked or rate-limited on corporate networks.",
            "samples": [],
        }


def iperf3_test(server, duration=10):
    if not server:
        return {
            "method": "iPerf3",
            "success": False,
            "target": "",
            "notes": "No iPerf3 server configured. Add iperf3_server in Settings.",
        }

    result = run_command(["iperf3", "-c", server, "-t", str(duration), "-J"], timeout=duration + 15)
    return {
        "method": "iPerf3",
        "target": server,
        "success": result.get("returncode") == 0,
        "raw": result,
        "notes": "Requires an iPerf3 server. Best for LAN/WAN throughput testing.",
    }


def quality_score(results):
    score = 100
    reasons = []
    successful = [r for r in results if r.get("success")]

    if not successful:
        return 0, ["No successful quality tests."]

    best_latency = min([r.get("avg_ms") for r in successful if r.get("avg_ms") is not None] or [999])
    worst_jitter = max([r.get("jitter_ms") for r in successful if r.get("jitter_ms") is not None] or [0])
    worst_loss = max([r.get("loss_percent") for r in successful if r.get("loss_percent") is not None] or [0])

    if best_latency > 150:
        score -= 30
        reasons.append("High latency.")
    elif best_latency > 75:
        score -= 15
        reasons.append("Moderate latency.")
    elif best_latency > 40:
        score -= 5
        reasons.append("Slightly elevated latency.")

    if worst_jitter > 50:
        score -= 25
        reasons.append("High jitter.")
    elif worst_jitter > 20:
        score -= 12
        reasons.append("Moderate jitter.")
    elif worst_jitter > 8:
        score -= 5
        reasons.append("Slightly elevated jitter.")

    if worst_loss > 10:
        score -= 35
        reasons.append("High connection failure/loss.")
    elif worst_loss > 2:
        score -= 15
        reasons.append("Some connection failure/loss.")

    failed_methods = [r["method"] for r in results if not r.get("success")]
    if failed_methods:
        score -= min(15, len(failed_methods) * 3)
        reasons.append(f"Some methods failed: {', '.join(failed_methods)}.")

    score = max(0, min(100, score))

    if not reasons:
        reasons.append("Connection quality looks healthy.")

    return score, reasons


def score_label(score):
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Poor"
    return "Bad"


def print_method_result(result):
    table = Table(title=f"{result.get('method')} — {result.get('target')}")
    table.add_column("Metric")
    table.add_column("Value")

    fields = [
        ("Success", "success"),
        ("Attempts", "attempts"),
        ("Successful Attempts", "successful_attempts"),
        ("Failed Attempts", "failed_attempts"),
        ("Loss / Failure", "loss_percent"),
        ("Minimum", "min_ms"),
        ("Average", "avg_ms"),
        ("Maximum", "max_ms"),
        ("Jitter", "jitter_ms"),
        ("Avg DNS", "avg_dns_ms"),
        ("Avg TCP", "avg_tcp_ms"),
        ("Avg TLS", "avg_tls_ms"),
        ("Avg First Byte", "avg_first_byte_ms"),
    ]

    for label, key in fields:
        if key in result and result.get(key) is not None:
            value = result.get(key)
            if key.endswith("_ms") or key in ["min_ms", "avg_ms", "max_ms", "jitter_ms"]:
                value = f"{value} ms"
            elif key == "loss_percent":
                value = f"{value}%"
            table.add_row(label, str(value))

    if result.get("error"):
        table.add_row("Error", str(result["error"]))

    table.add_row("Notes", str(result.get("notes", "")))
    console.print(table)


def connection_quality_test(config):
    host = config.get("connection_quality_host", "cloudflare.com")
    ip = config.get("connection_quality_ip", "1.1.1.1")
    port = _safe_int(config.get("connection_quality_port", 443), 443)
    url = config.get("connection_quality_url", "https://cloudflare.com")
    attempts = _safe_int(config.get("connection_quality_attempts", 10), 10)
    timeout = _safe_float(config.get("connection_quality_timeout_seconds", 3), 3)
    preferred = str(config.get("connection_quality_preferred_method", "auto")).lower()
    dns_domain = config.get("connection_quality_dns_domain", "google.com")
    dns_server = config.get("connection_quality_dns_server", "1.1.1.1")
    iperf_server = config.get("iperf3_server", "")
    iperf_duration = _safe_int(config.get("iperf3_duration_seconds", 10), 10)

    console.print(Panel.fit(
        "[bold cyan]Connection Quality Test[/bold cyan]\n"
        "Uses TCP/HTTPS/DNS/ICMP/iPerf methods so corporate ICMP blocking does not ruin your day.",
        border_style="cyan"
    ))

    method_map = {
        "tcp": lambda: tcp_connect_test(ip or host, port, attempts, timeout),
        "https": lambda: https_request_test(url, attempts, timeout),
        "dns": lambda: dns_latency_test(dns_domain, dns_server, attempts, timeout),
        "icmp": lambda: icmp_test(ip or host, attempts, timeout),
        "iperf3": lambda: iperf3_test(iperf_server, iperf_duration),
    }

    if preferred in ["tcp", "https", "dns", "icmp", "iperf3"]:
        methods = [preferred]
    elif preferred == "all":
        methods = ["tcp", "https", "dns", "icmp", "iperf3"]
    else:
        methods = ["tcp", "https", "dns", "icmp"]
        if iperf_server:
            methods.append("iperf3")

    results = []
    for method in methods:
        console.print(f"\n[cyan]Running {method.upper()} test...[/cyan]")
        result = method_map[method]()
        results.append(result)
        print_method_result(result)

    score, reasons = quality_score(results)

    summary = Table(title="Network Health Score")
    summary.add_column("Item")
    summary.add_column("Result")
    summary.add_row("Score", f"{score}/100")
    summary.add_row("Rating", score_label(score))
    summary.add_row("Best Available Method", next((r["method"] for r in results if r.get("success")), "None"))
    summary.add_row("Notes", " ".join(reasons))
    console.print(summary)

    return {
        "test": "connection_quality",
        "score": score,
        "rating": score_label(score),
        "reasons": reasons,
        "methods_run": methods,
        "results": results,
        "settings": {
            "host": host,
            "ip": ip,
            "port": port,
            "url": url,
            "attempts": attempts,
            "timeout": timeout,
            "preferred_method": preferred,
            "dns_domain": dns_domain,
            "dns_server": dns_server,
            "iperf3_server": iperf_server,
            "iperf3_duration": iperf_duration,
        },
    }
