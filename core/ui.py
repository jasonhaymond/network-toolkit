"""
Shared UI helpers.

Menus should look like they belong to the same application, not like several
unrelated scripts met in a parking lot and formed a committee.
"""

from rich.table import Table


MENU_HEADER_STYLE = "bold cyan"
MENU_NUMBER_STYLE = "bold cyan"
MENU_TEXT_STYLE = "white"


def menu_table(title):
    """Create a consistently styled menu table."""
    table = Table(
        title=title,
        show_header=True,
        header_style=MENU_HEADER_STYLE,
        border_style="blue",
        title_style="bold cyan",
    )
    table.add_column("#", style=MENU_NUMBER_STYLE, justify="right", width=4)
    table.add_column("Option", style=MENU_TEXT_STYLE)
    return table


def add_menu_options(table, options):
    """Add numbered menu options, then a spacer and 0 exit/return row.

    options should be a list of labels. Numbering starts at 1.
    """
    for i, item in enumerate(options, start=1):
        table.add_row(str(i), item)

    table.add_row("", "")
    table.add_row("0", "Exit / Return")
    return table


def add_zero_row(table, label="Exit / Return"):
    """Add a blank spacer row followed by a 0 row."""
    table.add_row("", "")
    table.add_row("0", label)
    return table
