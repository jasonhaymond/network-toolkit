from __future__ import annotations
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "settings.yaml"

DEFAULT_SETTINGS = {
    "ping_target": "8.8.8.8",
    "secondary_ping_target": "1.1.1.1",
    "dns_server": "1.1.1.1",
    "dns_test_domain": "google.com",
    "default_subnet": "auto",
    "logging_enabled": True,
    "monitoring_interval_seconds": 5,
    "report_export_path": "reports/",
    "packet_capture_path": "captures/",
    "preferred_interface": "auto",
    "startup_dependency_audit": True,
    "auto_install_dependencies": "ask",
}

def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()
    with SETTINGS_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    merged = DEFAULT_SETTINGS.copy()
    merged.update(data)
    return merged

def save_settings(settings: dict) -> None:
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, sort_keys=False)
