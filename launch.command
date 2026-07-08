#!/bin/bash

########################################
# Network Toolkit macOS Bootstrap Launcher
########################################

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

# Fix launch.sh permission after ZIP extraction if needed.
chmod +x "$SCRIPT_DIR/launch.sh" 2>/dev/null

exec "$SCRIPT_DIR/launch.sh"
