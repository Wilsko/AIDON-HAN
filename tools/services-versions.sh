#!/bin/bash
# Show versions of all HAN services

SERVICES=("sensor-reader" "gpio-switch-reader" "mgmt-data-reader" "han-api" "watchdog")
param=""
echo "=== HAN Services versions ==="
for svc in "${SERVICES[@]}"; do
    echo "$svc version"
	param="/opt/hservice/"
	param+=$svc
	param+=".py --version"
	sudo python3 $param
done
