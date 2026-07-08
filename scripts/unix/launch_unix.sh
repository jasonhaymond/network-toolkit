#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

run_toolkit() {
    install_python_requirements || exit 1
    echo ""
    echo "Starting Network Toolkit..."
    echo ""
    "$PYTHON_BIN" "$PROJECT_DIR/main.py"
    EXIT_CODE=$?
    echo ""
    echo "Network Toolkit exited."
    echo ""
    exit $EXIT_CODE
}

run_toolkit_admin() {
    install_python_requirements || exit 1
    echo ""
    echo "Starting Network Toolkit in Administrator Mode..."
    echo "You may be prompted for your password."
    echo ""
    sudo "$PYTHON_BIN" "$PROJECT_DIR/main.py"
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
            install_python_requirements || exit 1
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
        1) run_toolkit ;;
        2) run_toolkit_admin ;;
        3)
            install_python_requirements || exit 1
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
