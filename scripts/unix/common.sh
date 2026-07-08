#!/bin/bash

########################################
# Network Toolkit Unix Shared Helpers
########################################

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

print_header() {
    clear
    echo ""
    echo "======================================"
    echo " Network Toolkit"
    echo "======================================"
    echo ""
}

detect_os() {
    uname -s
}

ensure_python3() {
    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: Python 3 is not installed or not in PATH."
        echo ""
        echo "macOS:"
        echo "  brew install python"
        echo ""
        echo "Ubuntu/Debian:"
        echo "  sudo apt install python3 python3-venv python3-pip"
        return 1
    fi
}

create_venv() {
    ensure_python3 || return 1

    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR" || {
            echo ""
            echo "Failed to create virtual environment."
            echo "Ubuntu/Debian fix:"
            echo "  sudo apt install python3-venv"
            return 1
        }
    fi

    if [ ! -x "$PYTHON_BIN" ]; then
        echo "ERROR: Virtual environment Python not found at:"
        echo "  $PYTHON_BIN"
        echo ""
        echo "Try:"
        echo "  rm -rf .venv"
        echo "  ./install.sh"
        return 1
    fi
}

install_python_requirements() {
    create_venv || return 1

    echo "Upgrading pip/setuptools/wheel..."
    "$PYTHON_BIN" -m ensurepip --upgrade >/dev/null 2>&1 || true
    "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel || return 1

    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        echo "ERROR: requirements.txt not found."
        return 1
    fi

    echo "Installing Python requirements..."
    "$PYTHON_BIN" -m pip install -r "$PROJECT_DIR/requirements.txt" || return 1
}

fix_permissions() {
    chmod +x "$PROJECT_DIR/launch.sh" 2>/dev/null || true
    chmod +x "$PROJECT_DIR/launch.command" 2>/dev/null || true
    chmod +x "$PROJECT_DIR/install.sh" 2>/dev/null || true
    chmod +x "$PROJECT_DIR/scripts/unix/"*.sh 2>/dev/null || true
}

install_system_packages() {
    OS_NAME="$(detect_os)"

    case "$OS_NAME" in
        Darwin)
            install_macos_packages
            ;;
        Linux)
            install_linux_packages
            ;;
        *)
            echo "Unsupported Unix-like OS: $OS_NAME"
            ;;
    esac
}

install_macos_packages() {
    echo "Detected macOS."

    if ! xcode-select -p >/dev/null 2>&1; then
        echo "Installing Apple Command Line Tools..."
        xcode-select --install || true
        echo ""
        echo "After Command Line Tools finish installing, run ./install.sh again."
        exit 0
    fi

    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew is not installed."
        echo ""
        echo "Install Homebrew from https://brew.sh, then rerun:"
        echo "  ./install.sh"
        echo ""
        echo "Homebrew install command:"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        return 1
    fi

    echo "Installing/updating Homebrew packages..."
    brew update || true
    brew install python git nmap lldpd iperf3 arp-scan speedtest-cli || true
}

install_linux_packages() {
    echo "Detected Linux."

    if command -v apt >/dev/null 2>&1; then
        echo "Installing apt packages..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv git nmap lldpd wireless-tools iw net-tools iproute2 dnsutils iperf3 tcpdump network-manager curl unzip
        sudo systemctl enable --now lldpd || true
    else
        echo "This installer currently supports apt-based Linux distros."
        echo "Install Python 3, python3-venv, git, nmap, lldpd, iw, nmcli, and tcpdump manually."
    fi
}

show_status() {
    print_header
    echo "Project Path: $PROJECT_DIR"
    echo "Platform: $(detect_os)"
    echo "Python 3: $(command -v python3 || echo 'not found')"

    if [ -x "$PYTHON_BIN" ]; then
        echo "Venv Python: $("$PYTHON_BIN" --version 2>/dev/null)"
        echo "Virtual Environment: OK"
    else
        echo "Virtual Environment: Missing"
    fi

    if [ -f "$PROJECT_DIR/main.py" ]; then
        echo "main.py: OK"
    else
        echo "main.py: Missing"
    fi

    echo ""
}
