#!/bin/bash

########################################
# Network Toolkit Single Launcher
########################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

VENV_DIR=".venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

print_header() {
    clear
    echo ""
    echo "======================================"
    echo " Network Toolkit Launcher"
    echo "======================================"
    echo ""
}

ensure_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: Python 3 is not installed or not in PATH."
        echo "Install Python 3, then run this launcher again."
        exit 1
    fi
}

ensure_venv() {
    ensure_python
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
}

install_requirements() {
    ensure_venv

    echo "Checking/updating pip..."
    "$PYTHON_BIN" -m pip install -q --upgrade pip

    if [ -f "requirements.txt" ]; then
        echo "Installing/updating requirements..."
        "$PIP_BIN" install -q -r requirements.txt
    else
        echo "WARNING: requirements.txt not found."
    fi
}

show_status() {
    print_header
    echo "Project Path: $SCRIPT_DIR"
    echo "Platform: $(uname -s)"
    echo "Python 3: $(command -v python3 || echo 'not found')"

    if [ -x "$PYTHON_BIN" ]; then
        echo "Venv Python: $("$PYTHON_BIN" --version 2>/dev/null)"
        echo "Virtual Environment: OK"
    else
        echo "Virtual Environment: Missing"
    fi

    if [ -f "main.py" ]; then
        echo "main.py: OK"
    else
        echo "main.py: Missing"
    fi

    echo ""
}

run_toolkit() {
    install_requirements
    echo ""
    echo "Starting Network Toolkit..."
    echo ""
    "$PYTHON_BIN" main.py
    EXIT_CODE=$?
    echo ""
    echo "Network Toolkit exited."
    echo ""
    exit $EXIT_CODE
}

run_toolkit_admin() {
    install_requirements
    echo ""
    echo "Starting Network Toolkit in Administrator Mode..."
    echo "You may be prompted for your macOS password."
    echo ""
    sudo "$PYTHON_BIN" main.py
    EXIT_CODE=$?
    echo ""
    echo "Network Toolkit exited."
    echo ""
    exit $EXIT_CODE
}

rebuild_venv() {
    echo ""
    echo "This will delete and rebuild the virtual environment."
    read -r -p "Continue? [y/N]: " CONFIRM

    case "$CONFIRM" in
        y|Y|yes|YES)
            rm -rf "$VENV_DIR"
            install_requirements
            echo ""
            echo "Virtual environment rebuilt."
            ;;
        *)
            echo "Cancelled."
            ;;
    esac
}

while true; do
    show_status

    echo "1) Start Network Toolkit"
    echo "2) Start Network Toolkit (Administrator Mode)"
    echo "3) Install/Update Dependencies"
    echo "4) Rebuild Virtual Environment"
    echo "5) Exit"
    echo ""

    read -r -p "Selection: " CHOICE

    case "$CHOICE" in
        1)
            run_toolkit
            ;;
        2)
            run_toolkit_admin
            ;;
        3)
            install_requirements
            echo ""
            echo "Dependencies updated."
            read -r -p "Press Enter to continue..."
            ;;
        4)
            rebuild_venv
            read -r -p "Press Enter to continue..."
            ;;
        5)
            echo ""
            echo "Goodbye."
            echo ""
            exit 0
            ;;
        *)
            echo "Invalid selection."
            sleep 1
            ;;
    esac
done
