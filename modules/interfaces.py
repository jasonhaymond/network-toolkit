from rich.console import Console
from rich.table import Table
from core.utils import interface_records, get_primary_interface_record

console = Console()


def _print_interface_table(records, title):
    table = Table(title=title)
    table.add_column("Interface")
    table.add_column("IP Address")
    table.add_column("Subnet")
    table.add_column("CIDR")
    table.add_column("MAC")
    table.add_column("Status")
    table.add_column("Speed")
    table.add_column("Hidden?")
    for record in records:
        table.add_row(record.get("interface", ""), record.get("ip_address", ""), record.get("subnet", ""), f"/{record.get('cidr')}" if record.get("cidr") != "" else "", record.get("mac", ""), record.get("status", ""), record.get("speed", ""), "Yes" if record.get("hidden_by_default") else "No")
    console.print(table)


def show_interfaces(include_unhelpful=False):
    records = interface_records(include_unhelpful=include_unhelpful)
    title = "Useful Interface / IP Information" if not include_unhelpful else "All Interface / IP Information"
    _print_interface_table(records, title)
    primary = get_primary_interface_record()
    if primary:
        console.print(f"\n[green]Primary/default connection:[/green] {primary['interface']} | {primary['ip_address']} | {primary['subnet']}")
    return records


def show_all_interfaces():
    return show_interfaces(include_unhelpful=True)
