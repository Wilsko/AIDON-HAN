#!/bin/bash
# Show status of all HAN services

SERVICES=("sensor-reader" "gpio-switch-reader" "mgmt-data-reader" "han-api" "watchdog")

echo "=== HAN Service Status ==="
for svc in "${SERVICES[@]}"; do
    printf "%-22s : " "$svc"
    systemctl is-active "$svc" >/dev/null 2>&1 && echo "active" || echo "inactive"
done
