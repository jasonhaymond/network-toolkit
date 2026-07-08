"""
Dependency check menu.

Runs a quick inventory of external commands the toolkit can use and shows
install suggestions for missing ones. It's basically a shopping list, but for
network tools instead of things humans pretend they will cook this week.
"""

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from core.dependencies import DEPENDENCIES, command_exists, explain_missing, offer_install
from core.ui import menu_table, add_zero_row

console = Console()


def dependency_check_menu():
    while True:
        console.clear()

        table = menu_table("Dependency Checks")
        table.add_row("1", "Show Dependency Status")
        table.add_row("2", "Install/Fix One Missing Tool")
        table.add_row("3", "Attempt to Install All Missing Supported Tools")
        add_zero_row(table, "Return to Main Menu")
        console.print(table)

        choice = Prompt.ask("Selection")

        if choice == "1":
            show_dependency_status()
            Prompt.ask("Press Enter to continue")
        elif choice == "2":
            install_one_missing()
        elif choice == "3":
            install_all_missing()
            Prompt.ask("Press Enter to continue")
        elif choice == "0":
            return None


def show_dependency_status():
    table = Table(title="External Tool Status", border_style="blue", header_style="bold cyan")
    table.add_column("Command", style="cyan")
    table.add_column("Status")
    table.add_column("Used For")

    results = []

    for command, dep in sorted(DEPENDENCIES.items()):
        found = command_exists(command)
        table.add_row(
            command,
            "[green]Installed[/green]" if found else "[red]Missing[/red]",
            dep.description or "",
        )
        results.append({
            "command": command,
            "installed": found,
            "description": dep.description,
        })

    console.print(table)
    return results


def install_one_missing():
    missing = [cmd for cmd in DEPENDENCIES if not command_exists(cmd)]

    if not missing:
        console.print("[green]No missing known dependencies. Miracles do happen.[/green]")
        Prompt.ask("Press Enter to continue")
        return None

    table = menu_table("Missing Tools")
    for i, cmd in enumerate(missing, start=1):
        table.add_row(str(i), cmd)
    add_zero_row(table, "Return")
    console.print(table)

    choice = Prompt.ask("Selection")

    if choice == "0":
        return None

    try:
        command = missing[int(choice) - 1]
    except Exception:
        console.print("[red]Invalid selection.[/red]")
        Prompt.ask("Press Enter to continue")
        return None

    offer_install(command)
    Prompt.ask("Press Enter to continue")
    return None


def install_all_missing():
    missing = [cmd for cmd in DEPENDENCIES if not command_exists(cmd)]

    if not missing:
        console.print("[green]No missing known dependencies.[/green]")
        return None

    for command in missing:
        console.print()
        console.print(f"[cyan]Checking missing tool:[/cyan] {command}")
        offer_install(command)

    return None
