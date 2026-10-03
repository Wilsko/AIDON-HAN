
#!/bin/bash
set -euo pipefail
# Require root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

CONFIG_FILE="alertmail.config"
TOOL_DIR="./tools"
SERVICE_DIR="/opt/hservice"
echo "Copying $TOOL_DIR/$CONFIG_FILE to $SERVICE_DIR/$CONFIG_FILE"
cp  "$TOOL_DIR/$CONFIG_FILE" "$SERVICE_DIR/"
echo "Setting $SERVICE_DIR/$CONFIG_FILE permissions"
chown hservice:hservice "$SERVICE_DIR/$CONFIG_FILE"
