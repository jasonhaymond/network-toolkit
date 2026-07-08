import platform
from rich.console import Console
from core.utils import run_command

console = Console()


def show_gateway():
    system = platform.system()
    console.print("[cyan]Gateway Information[/cyan]\n")

    if system == "Darwin":
        result = run_command(["route", "-n", "get", "default"])
    elif system == "Windows":
        result = run_command(["powershell", "-NoProfile", "-Command", "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Format-Table -AutoSize"])
        if result.get("returncode") not in (0, None) or not result.get("stdout"):
            result = run_command(["route", "print", "0.0.0.0"])
    else:
        result = run_command(["ip", "route", "show", "default"])

    console.print(result["stdout"] or result["stderr"])
    return result
