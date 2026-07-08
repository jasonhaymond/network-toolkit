from __future__ import annotations
from rich.console import Console
from core.config import load_settings, save_settings
from core.interrupts import prompt_input, OperationCancelled, cancel_message
console = Console()

def settings_menu() -> None:
    settings = load_settings()
    keys = list(settings.keys())
    while True:
        console.print("\n[cyan]Settings[/cyan]")
        for idx, key in enumerate(keys, 1):
            console.print(f"{idx}) {key}: {settings[key]}")
        console.print("0) Return")
        choice = prompt_input("Selection: ").strip()
        if choice == "0":
            save_settings(settings)
            return
        if not choice.isdigit() or not (1 <= int(choice) <= len(keys)):
            continue
        key = keys[int(choice)-1]
        new_value = prompt_input(f"New value for {key}: ").strip()
        if new_value.lower() in ("true", "false"):
            settings[key] = new_value.lower() == "true"
        elif new_value:
            settings[key] = new_value
        save_settings(settings)
