import platform
from rich.console import Console
from core.utils import run_command
from core.dependencies import require_command

console = Console()


def switch_port_info():
    system = platform.system()

    console.print("[cyan]Switch + Port Discovery[/cyan]\n")
    console.print("Uses local LLDP/CDP-style neighbor discovery when available. This does NOT require SNMP.\n")

    if system in ["Darwin", "Linux"]:
        if not require_command("lldpctl"):
            return {
                "collector": "lldpctl",
                "success": False,
                "error": "lldpctl is required for LLDP switch/port discovery and is not installed.",
                "missing_command": "lldpctl",
            }

        result = run_command(["sudo", "lldpctl"], timeout=30)
        if "command not found" in result.get("stderr", "").lower() or result.get("returncode") is None:
            install = "brew install lldpd" if system == "Darwin" else "sudo apt install lldpd && sudo systemctl enable --now lldpd"
            result["hint"] = install
            console.print(f"[yellow]lldpctl not found. Install/start with:[/yellow] {install}")
        else:
            console.print(result["stdout"] or result["stderr"])
        return result

    if system == "Windows":
        # Windows does not include a simple built-in LLDP neighbor display equivalent.
        result = {
            "collector": "Windows LLDP guidance",
            "stdout": "",
            "stderr": (
                "Windows does not provide a built-in lldpctl equivalent. "
                "Recommended options: install Wireshark/Npcap and capture LLDP frames, "
                "use vendor utilities, or add a future packet-capture LLDP parser."
            ),
            "suggestions": [
                "Install Wireshark with Npcap.",
                "Run toolkit as Administrator for future packet capture support.",
                "Capture ethertype 0x88cc for LLDP.",
            ],
        }
        console.print(f"[yellow]{result['stderr']}[/yellow]")
        return result

    return {"error": f"Unsupported platform: {system}"}
