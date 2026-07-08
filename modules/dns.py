from rich.console import Console
from core.utils import run_command

console = Console()


def dns_test(config):
    domain = config["dns_test_domain"]
    dns_server = config["dns_server"]

    console.print(f"[cyan]DNS Test[/cyan]")
    console.print(f"Domain: {domain}")
    console.print(f"DNS Server: {dns_server}\n")

    result = run_command(["nslookup", domain, dns_server])
    console.print(result["stdout"] or result["stderr"])

    result["domain"] = domain
    result["dns_server"] = dns_server
    return result
