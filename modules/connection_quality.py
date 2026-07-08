"""
Connection quality diagnostics.

This module replaces the old ICMP-only latency/jitter test with practical tests
that still work when corporate networks block ping, because apparently blocking
the simplest diagnostic known to humanity is now considered enterprise security.

Methods:
- TCP connect latency
- HTTPS request timing
- DNS lookup timing
- ICMP ping, when allowed
- iPerf3, when configured
"""

import socket
import ssl
import statistics
import subprocess
import time
from urllib.parse import urlparse

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from core.utils import run_command
from core.ui import menu_table, add_zero_row

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


def _safe_bool(value, default=True):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).lower() in ["true", "1", "yes", "y", "on"]


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


def config_values(config):
    return {
        "host": config.get("connection_quality_host", "cloudflare.com"),
        "ip": config.get("connection_quality_ip", "1.1.1.1"),
        "port": _safe_int(config.get("connection_quality_port", 443), 443),
        "url": config.get("connection_quality_url", "https://cloudflare.com"),
        "attempts": _safe_int(config.get("connection_quality_attempts", 10), 10),
        "timeout": _safe_float(config.get("connection_quality_timeout_seconds", 3), 3),
        "preferred": str(config.get("connection_quality_preferred_method", "auto")).lower(),
        "dns_domain": config.get("connection_quality_dns_domain", "google.com"),
        "dns_server": config.get("connection_quality_dns_server", "1.1.1.1"),
        "iperf_server": config.get("iperf3_server", ""),
        "iperf_duration": _safe_int(config.get("iperf3_duration_seconds", 10), 10),
    }


def score_inclusion_settings(config):
    return {
        "TCP Connect": _safe_bool(config.get("connection_quality_score_include_tcp", True), True),
        "HTTPS Request": _safe_bool(config.get("connection_quality_score_include_https", True), True),
        "DNS Lookup": _safe_bool(config.get("connection_quality_score_include_dns", True), True),
        "ICMP Ping": _safe_bool(config.get("connection_quality_score_include_icmp", False), False),
        "iPerf3": _safe_bool(config.get("connection_quality_score_include_iperf3", True), True),
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
    """Measure DNS lookup latency with robust fallbacks.

    Previous behavior used a single nslookup subprocess with the same short timeout
    used for network sockets. That can fail on corporate Windows machines because
    nslookup startup, policy inspection, DNS suffix handling, or security tooling can
    take longer than 3 seconds. Humans then run nslookup manually and it works,
    making the script look like it was assembled by raccoons. Not ideal.

    New behavior:
    1. Use the OS resolver via socket.getaddrinfo() first.
    2. If a DNS server is configured, also try nslookup with a safer timeout.
    3. Count the attempt successful if either method succeeds.
    """
    samples = []
    process_timeout = max(float(timeout) + 5, 8)

    for i in range(1, attempts + 1):
        errors = []
        start = time.perf_counter()
        success = False
        resolver_used = ""

        # First try the system resolver. This mirrors what most apps actually use.
        try:
            socket.getaddrinfo(domain, None)
            success = True
            resolver_used = "system resolver"
        except Exception as e:
            errors.append(f"system resolver: {e}")

        # If a DNS server is configured, try nslookup too. This gives direct-server
        # visibility without making the whole test fail when nslookup is weird.
        if dns_server:
            try:
                completed = subprocess.run(
                    ["nslookup", domain, dns_server],
                    capture_output=True,
                    text=True,
                    timeout=process_timeout,
                )

                combined_output = ((completed.stdout or "") + "\\n" + (completed.stderr or "")).strip()
                output_lower = combined_output.lower()

                # nslookup output varies by OS. Treat common positive signs as success.
                positive_markers = [
                    "name:",
                    "address:",
                    "addresses:",
                    "non-authoritative answer",
                ]
                negative_markers = [
                    "can't find",
                    "server failed",
                    "timed out",
                    "no response",
                    "non-existent domain",
                    "can't reach",
                ]

                has_positive = any(marker in output_lower for marker in positive_markers)
                has_negative = any(marker in output_lower for marker in negative_markers)

                if completed.returncode == 0 or (has_positive and not has_negative):
                    success = True
                    resolver_used = f"nslookup via {dns_server}" if not resolver_used else f"{resolver_used} + nslookup via {dns_server}"
                else:
                    errors.append(f"nslookup: {combined_output or 'no output'}")
            except Exception as e:
                errors.append(f"nslookup: {e}")

        latency = (time.perf_counter() - start) * 1000

        if success:
            samples.append({
                "sample": i,
                "success": True,
                "latency_ms": round(latency, 2),
                "resolver_used": resolver_used,
                "error": "",
            })
        else:
            samples.append({
                "sample": i,
                "success": False,
                "latency_ms": None,
                "resolver_used": "",
                "error": " | ".join(errors),
            })

    target = f"{domain} via system resolver"
    if dns_server:
        target += f" + {dns_server}"

    result = summarize_samples(samples)
    result.update({
        "method": "DNS Lookup",
        "target": target,
        "notes": (
            "Measures DNS resolution time. Uses system resolver first and nslookup as "
            "a direct-server fallback so corporate DNS/security delay does not cause false failures."
        ),
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


def quality_score(results, included_methods=None):
    score = 100
    reasons = []

    included_methods = included_methods or {}
    scored_results = [r for r in results if included_methods.get(r.get("method"), True)]
    excluded_results = [r for r in results if not included_methods.get(r.get("method"), True)]

    if not scored_results:
        return 0, ["No tests are included in the health score."], excluded_results

    successful = [r for r in scored_results if r.get("success")]
    if not successful:
        return 0, ["No successful included quality tests."], excluded_results

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

    failed_methods = [r["method"] for r in scored_results if not r.get("success")]
    if failed_methods:
        score -= min(15, len(failed_methods) * 3)
        reasons.append(f"Some included methods failed: {', '.join(failed_methods)}.")

    if excluded_results:
        reasons.append("Excluded from score: " + ", ".join(r.get("method", "Unknown") for r in excluded_results) + ".")

    score = max(0, min(100, score))

    if not reasons:
        reasons.append("Connection quality looks healthy.")

    return score, reasons, excluded_results


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


def print_method_result(result, included_in_score=True):
    title = f"{result.get('method')} — {result.get('target')}"
    if not included_in_score:
        title += " (Excluded from Health Score)"

    table = Table(title=title)
    table.add_column("Metric")
    table.add_column("Value")

    fields = [
        ("Included in Health Score", "included_in_score"),
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

    result["included_in_score"] = included_in_score

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


def run_named_method(method, config):
    values = config_values(config)

    if method == "tcp":
        return tcp_connect_test(values["ip"] or values["host"], values["port"], values["attempts"], values["timeout"])
    if method == "https":
        return https_request_test(values["url"], values["attempts"], values["timeout"])
    if method == "dns":
        return dns_latency_test(values["dns_domain"], values["dns_server"], values["attempts"], values["timeout"])
    if method == "icmp":
        return icmp_test(values["ip"] or values["host"], values["attempts"], values["timeout"])
    if method == "iperf3":
        return iperf3_test(values["iperf_server"], values["iperf_duration"])

    raise ValueError(f"Unknown connection quality method: {method}")


def connection_quality_test(config, methods_override=None):
    values = config_values(config)
    preferred = values["preferred"]
    included = score_inclusion_settings(config)

    console.print(Panel.fit(
        "[bold cyan]Connection Quality Test[/bold cyan]\n"
        "Uses TCP/HTTPS/DNS/ICMP/iPerf methods so corporate ICMP blocking does not ruin your day.",
        border_style="cyan"
    ))

    if methods_override:
        methods = methods_override
    elif preferred in ["tcp", "https", "dns", "icmp", "iperf3"]:
        methods = [preferred]
    elif preferred == "all":
        methods = ["tcp", "https", "dns", "icmp", "iperf3"]
    else:
        methods = ["tcp", "https", "dns", "icmp"]
        if values["iperf_server"]:
            methods.append("iperf3")

    method_display = {
        "tcp": "TCP Connect",
        "https": "HTTPS Request",
        "dns": "DNS Lookup",
        "icmp": "ICMP Ping",
        "iperf3": "iPerf3",
    }

    results = []
    for method in methods:
        console.print(f"\n[cyan]Running {method.upper()} test...[/cyan]")
        result = run_named_method(method, config)
        included_in_score = included.get(method_display.get(method, result.get("method")), True)
        result["included_in_score"] = included_in_score
        results.append(result)
        print_method_result(result, included_in_score=included_in_score)

    score, reasons, excluded = quality_score(results, included)

    summary = Table(title="Network Health Score")
    summary.add_column("Item")
    summary.add_column("Result")
    summary.add_row("Score", f"{score}/100")
    summary.add_row("Rating", score_label(score))
    summary.add_row("Best Available Included Method", next((r["method"] for r in results if r.get("success") and r.get("included_in_score")), "None"))
    summary.add_row("Notes", " ".join(reasons))
    console.print(summary)

    return {
        "test": "connection_quality",
        "score": score,
        "rating": score_label(score),
        "reasons": reasons,
        "methods_run": methods,
        "score_inclusion": included,
        "excluded_methods": [r.get("method") for r in excluded],
        "results": results,
        "settings": values,
    }


def connection_quality_submenu(config):
    while True:
        console.clear()
        table = menu_table("Connection Tests")

        options = [
            ("1", "Run Auto Quality Test"),
            ("2", "Run All Tests"),
            ("3", "TCP Connect Test"),
            ("4", "HTTPS Request Test"),
            ("5", "DNS Lookup Test"),
            ("6", "ICMP Ping Test"),
            ("7", "iPerf3 Test"),
            ("8", "Show Score Inclusion Settings"),
        ]

        for key, label in options:
            table.add_row(key, label)

        add_zero_row(table, "Return to Main Menu")
        console.print(table)

        choice = Prompt.ask("Selection")

        if choice == "1":
            return connection_quality_test(config)
        if choice == "2":
            return connection_quality_test(config, methods_override=["tcp", "https", "dns", "icmp", "iperf3"])
        if choice == "3":
            return connection_quality_test(config, methods_override=["tcp"])
        if choice == "4":
            return connection_quality_test(config, methods_override=["https"])
        if choice == "5":
            return connection_quality_test(config, methods_override=["dns"])
        if choice == "6":
            return connection_quality_test(config, methods_override=["icmp"])
        if choice == "7":
            return connection_quality_test(config, methods_override=["iperf3"])
        if choice == "8":
            included = score_inclusion_settings(config)
            settings_table = Table(title="Health Score Inclusion Settings")
            settings_table.add_column("Method")
            settings_table.add_column("Included?")
            for method, enabled in included.items():
                settings_table.add_row(method, "Yes" if enabled else "No")
            console.print(settings_table)
            console.print("\n[yellow]Change these in Settings or settings.yaml.[/yellow]")
            Prompt.ask("Press Enter to continue")
        if choice == "0":
            return None
