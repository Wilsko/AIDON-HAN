#!/bin/bash
# Enable and start HAN services (idempotent)

PYTHON_SCRIPTS=("sensor-reader.py" "gpio-switch-reader.py" "mgmt-data-reader.py" "han-api.py" "watchdog.py")

echo "=== Enabling and starting services: $(date) ==="

for script in "${PYTHON_SCRIPTS[@]}"; do
    SERVICE_NAME="${script%.py}"

    echo "Processing: $SERVICE_NAME"

    # Enable if not enabled
    if systemctl is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
        echo "Already enabled"
    else
        echo "Enabling"
        systemctl enable "$SERVICE_NAME"
    fi

    # Start or restart
    if systemctl is-active "$SERVICE_NAME" >/dev/null 2>&1; then
        echo "Restarting"
        systemctl restart "$SERVICE_NAME"
    else
        echo "Starting"
        systemctl start "$SERVICE_NAME"
    fi
done

echo "=== Service activation complete: $(date) ==="
