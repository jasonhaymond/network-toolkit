#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "========================================"
echo "Network Toolkit Launcher - macOS/Linux"
echo "========================================"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt
python main.py
