#!/bin/bash
set -euo pipefail
# Require root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

TOOL_DIR="./tools"

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

while true; do
    clear
    echo "======================================================"
    echo "      HAN Alert mail and parameters config tool"
	echo "      Edit and test alertmail.config"
	echo "======================================================"
    echo
    echo " 1) Edit config file"
    echo " 2) Send alert mail using test config"
	echo " 3) Deploy config to production"
    echo " E) Exit"
    echo
    read -p "Select an option: " choice

    case "$choice" in
        1) run_tool "editconfigfile.sh" ;;
        3) run_tool "saveconfigfile.sh" ;;		
		2) run_tool "sendalertmail-test.py" ;;
        E) echo "Exiting."; exit 0 ;;
        e) echo "Exiting."; exit 0 ;;
        *) echo "Invalid choice. Press Enter."; read ;;
    esac
done