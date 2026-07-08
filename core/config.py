"""
Configuration helper for Network Toolkit.

This module owns settings.yaml loading/saving and the Settings menu.
Keeping this separate prevents every diagnostic module from inventing its own
tiny configuration kingdom. History has shown tiny kingdoms still start wars.
"""

import yaml
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt

console = Console()
CONFIG_FILE = Path("settings.yaml")

DEFAULT_CONFIG = {
    "ping_target": "8.8.8.8",
    "secondary_ping_target": "1.1.1.1",
    "dns_server": "1.1.1.1",
    "dns_test_domain": "google.com",
    "default_subnet": "auto",
    "monitoring_interval_seconds": 5,
    "logging_enabled": True,
    "report_export_path": "reports",
    "hide_unhelpful_interfaces": True,
    "show_sensitive_wifi_identifiers": True,
    "wifi_collector_priority": "corewlan",
    "connection_quality_host": "cloudflare.com",
    "connection_quality_ip": "1.1.1.1",
    "connection_quality_port": 443,
    "connection_quality_url": "https://cloudflare.com",
    "connection_quality_attempts": 10,
    "connection_quality_timeout_seconds": 3,
    "connection_quality_preferred_method": "auto",
    "connection_quality_dns_domain": "google.com",
    "connection_quality_dns_server": "1.1.1.1",
    "iperf3_server": "",
    "iperf3_duration_seconds": 10,
    "connection_quality_score_include_tcp": True,
    "connection_quality_score_include_https": True,
    "connection_quality_score_include_dns": True,
    "connection_quality_score_include_icmp": False,
    "connection_quality_score_include_iperf3": True,


}


def load_config():
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    config = DEFAULT_CONFIG.copy()
    config.update(loaded)
    return config


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        yaml.dump(config, file, sort_keys=False)


def settings_menu():
    config = load_config()
    while True:
        console.clear()
        console.print("[cyan]Settings[/cyan]\n")
        console.print("[dim]Tip: set default_subnet to auto for dynamic primary-network detection.[/dim]\n")
        keys = list(config.keys())
        for i, key in enumerate(keys, start=1):
            console.print(f"{i}) {key}: [green]{config[key]}[/green]")
        console.print("")
        console.print("0) Return")
        choice = Prompt.ask("Selection")
        if choice == "0":
            save_config(config)
            return
        try:
            key = keys[int(choice) - 1]
        except Exception:
            continue
        new_value = Prompt.ask(f"New value for {key}")
        if isinstance(config[key], bool):
            config[key] = new_value.lower() in ["true", "yes", "1", "y"]
        elif isinstance(config[key], int):
            config[key] = int(new_value)
        else:
            config[key] = new_value
        save_config(config)
