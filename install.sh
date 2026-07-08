#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

OS_NAME="$(uname -s)"
VENV_DIR=".venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

echo ""
echo "======================================"
echo " Network Toolkit Installer"
echo "======================================"
echo ""

install_macos_packages() {
    echo "Detected macOS."

    if ! xcode-select -p >/dev/null 2>&1; then
        echo "Installing Apple Command Line Tools..."
        xcode-select --install || true
        echo "After Command Line Tools finish installing, run ./install.sh again."
        exit 0
    fi

    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew is not installed."
        echo "Install Homebrew from https://brew.sh, then rerun this installer."
        echo ""
        echo 'Homebrew install command:'
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        exit 1
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

ensure_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: python3 is not available."
        exit 1
    fi
}

create_venv() {
    ensure_python

    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR" || {
            echo ""
            echo "Failed to create virtual environment."
            echo "On Ubuntu/Debian, install venv with:"
            echo "  sudo apt install python3-venv"
            exit 1
        }
    fi

    echo "Upgrading pip/setuptools/wheel..."
    "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

    echo "Installing Python requirements..."
    "$PIP_BIN" install -r requirements.txt
}

fix_permissions() {
    chmod +x launch.sh 2>/dev/null || true
    chmod +x launch.command 2>/dev/null || true
    chmod +x install.sh 2>/dev/null || true
}

case "$OS_NAME" in
    Darwin) install_macos_packages ;;
    Linux) install_linux_packages ;;
    *) echo "Unsupported OS for install.sh: $OS_NAME" ;;
esac

create_venv
fix_permissions

echo ""
echo "Installation complete."
echo "Start the toolkit with:"
echo "  ./launch.sh"
echo ""
