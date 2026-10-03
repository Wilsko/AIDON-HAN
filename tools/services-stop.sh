#!/bin/bash
# Stop all HAN services

SERVICES=("sensor-reader" "gpio-switch-reader" "mgmt-data-reader" "han-api" "watchdog")

echo "=== Stopping HAN Services ==="
for svc in "${SERVICES[@]}"; do
    echo "Stopping $svc"
    systemctl stop "$svc" 2>/dev/null
done
