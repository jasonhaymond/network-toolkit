#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
chmod +x "$SCRIPT_DIR/launch.sh" 2>/dev/null
chmod +x "$SCRIPT_DIR/install.sh" 2>/dev/null
chmod +x "$SCRIPT_DIR/scripts/unix/"*.sh 2>/dev/null
exec "$SCRIPT_DIR/launch.sh"
