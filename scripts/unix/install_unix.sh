#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

print_header
echo "Running Unix installer..."
echo ""

install_system_packages || true
install_python_requirements || exit 1
fix_permissions

echo ""
echo "Installation complete."
echo ""
echo "Start the toolkit with:"
echo "  ./launch.sh"
echo ""
