import platform
import re
from rich.console import Console
from rich.table import Table
from core.utils import run_command
from core.dependencies import require_command

console = Console()


def internet_test(config):
    target = config["ping_target"]
    system = platform.system()
    console.print(f"[cyan]Internet Reachability[/cyan]")
    console.print(f"Ping Target: {target}\n")
    command = ["ping", "-n", "4", target] if system == "Windows" else ["ping", "-c", "4", target]
    result = run_command(command)
    console.print(result["stdout"] or result["stderr"])
    result["target"] = target
    return result


def parse_speedtest(output):
    data = {"testing_provider": "", "public_ip": "", "test_server": "", "server_distance": "", "connection_ms": "", "download_mbps": "", "upload_mbps": "", "raw_output": output}
    provider_match = re.search(r"Testing from (.*?) \((.*?)\)", output)
    if provider_match:
        data["testing_provider"] = provider_match.group(1)
        data["public_ip"] = provider_match.group(2)
    server_match = re.search(r"Hosted by (.*?) \[(.*?)\]: ([\d.]+) ms", output)
    if server_match:
        data["test_server"] = server_match.group(1)
        data["server_distance"] = server_match.group(2)
        data["connection_ms"] = float(server_match.group(3))
    download_match = re.search(r"Download:\s+([\d.]+)\s+Mbit/s", output)
    if download_match:
        data["download_mbps"] = float(download_match.group(1))
    upload_match = re.search(r"Upload:\s+([\d.]+)\s+Mbit/s", output)
    if upload_match:
        data["upload_mbps"] = float(upload_match.group(1))
    return data


def speed_test():
    console.print("[cyan]Internet Speed Test[/cyan]\n")
    if not require_command("speedtest-cli"):
        return {
            "tool": "internet_speed_test",
            "success": False,
            "error": "speedtest-cli is required for this speed test and is not installed.",
            "missing_command": "speedtest-cli",
        }

    result = run_command(["speedtest-cli"], timeout=120)
    if result["stdout"]:
        parsed = parse_speedtest(result["stdout"])
        table = Table(title="Internet Speed Test Summary")
        table.add_column("Item")
        table.add_column("Result")
        rows = [("Testing Provider", parsed.get("testing_provider", "")), ("Public IP", parsed.get("public_ip", "")), ("Test Server", parsed.get("test_server", "")), ("Server Distance", parsed.get("server_distance", "")), ("Connection / Ping", f"{parsed.get('connection_ms')} ms" if parsed.get("connection_ms") != "" else ""), ("Download", f"{parsed.get('download_mbps')} Mbps" if parsed.get("download_mbps") != "" else ""), ("Upload", f"{parsed.get('upload_mbps')} Mbps" if parsed.get("upload_mbps") != "" else "")]
        for label, value in rows:
            table.add_row(label, str(value))
        console.print(table)
        return {"command": result["command"], "returncode": result["returncode"], "summary": parsed, "raw_output": result["stdout"], "stderr": result["stderr"]}
    console.print(result["stderr"])
    return result
