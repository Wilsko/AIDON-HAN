#!/bin/bash
set -euo pipefail
# Require root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

# Helper to run a tool safely
run_tool() {
    local tool="$1"

    clear
    echo "=== Running $tool ==="
    echo

    if [ ! -f "$TOOL_DIR/$tool" ]; then
        echo "ERROR: $tool not found in $TOOL_DIR"
        echo "Press Enter to return to menu"
        read
        return
    fi

    case "$tool" in
        *.py)
            python3 "$TOOL_DIR/$tool"
            ;;
        *.sh)
            bash "$TOOL_DIR/$tool"
            ;;
        *)
            echo "ERROR: Unknown file type for $tool"
            ;;
    esac

    echo
    echo "--- $tool finished ---"
    echo "Press Enter to return to menu"
    read
}

CONFIG_FILE="alertmail.config"
TOOL_DIR="./tools"
SERVICE_DIR="/opt/hservice"
# cp  "$SERVICE_DIR/$CONFIG_FILE" "$TOOL_DIR"
nano "$TOOL_DIR/$CONFIG_FILE"
