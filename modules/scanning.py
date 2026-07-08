import re
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from core.utils import run_command, get_dynamic_subnet

console = Console()


def parse_nmap_ping_scan(output):
    hosts = []
    current = None
    report_re = re.compile(r"Nmap scan report for (?:(.*?) )?\(?(\d+\.\d+\.\d+\.\d+)\)?")
    latency_re = re.compile(r"Host is up(?: \(([\d.]+)s latency\))?")
    mac_re = re.compile(r"MAC Address:\s+([0-9A-Fa-f:]{17})(?: \((.*?)\))?")
    for line in output.splitlines():
        report_match = report_re.search(line)
        if report_match:
            if current:
                hosts.append(current)
            hostname = (report_match.group(1) or "").strip()
            ip = report_match.group(2)
            current = {"ip": ip, "hostname": hostname if hostname != ip else "", "mac": "", "vendor": "", "status": "unknown", "latency_ms": ""}
            continue
        if current:
            latency_match = latency_re.search(line)
            if latency_match:
                current["status"] = "up"
                if latency_match.group(1):
                    current["latency_ms"] = round(float(latency_match.group(1)) * 1000, 2)
            mac_match = mac_re.search(line)
            if mac_match:
                current["mac"] = mac_match.group(1)
                current["vendor"] = mac_match.group(2) or ""
    if current:
        hosts.append(current)
    return hosts


def subnet_scan(config):
    configured = config.get("default_subnet", "auto")
    dynamic_subnet = get_dynamic_subnet()
    default_subnet = dynamic_subnet if configured == "auto" and dynamic_subnet else configured
    subnet = Prompt.ask("Subnet to scan", default=default_subnet)
    console.print(f"[cyan]Subnet Scan: {subnet}[/cyan]\n")
    console.print("[dim]Tip: MAC addresses usually require local subnet access and may need sudo/nmap privileges.[/dim]\n")
    result = run_command(["nmap", "-sn", subnet], timeout=180)
    hosts = parse_nmap_ping_scan(result["stdout"])
    if hosts:
        table = Table(title=f"Subnet Scan Results: {subnet}")
        table.add_column("IP")
        table.add_column("Hostname")
        table.add_column("MAC")
        table.add_column("Vendor")
        table.add_column("Status")
        table.add_column("Latency")
        for host in hosts:
            latency = f"{host['latency_ms']} ms" if host["latency_ms"] != "" else ""
            table.add_row(host.get("ip", ""), host.get("hostname", ""), host.get("mac", ""), host.get("vendor", ""), host.get("status", ""), latency)
        console.print(table)
        console.print(f"\n[green]{len(hosts)} host(s) up[/green]")
    else:
        console.print(result["stdout"] or result["stderr"])
    return {"command": result["command"], "returncode": result["returncode"], "subnet": subnet, "hosts_up": len(hosts), "hosts": hosts, "raw_output": result["stdout"], "stderr": result["stderr"]}
