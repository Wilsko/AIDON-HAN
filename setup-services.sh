#!/bin/bash
# This script is used to create systemd services for the python scripts
# It is run on the server after the scripts are copied there
# 7.5.2025 VP han-api service cannot access databases or files defined in python progrems without full path
# Logs are not found from  var/log/hservice/
# service definitions in systemd directory seem to be valid 
# must check service account permissions and default directory
# Define service account
SERVICE_USER="hservice"

# Create the service user without a home directory
sudo useradd -r -s /bin/false $SERVICE_USER

# Define the Python scripts and services
PYTHON_SCRIPTS=("sensor-reader.py" "gpio-switch-reader.py" "mgmt-data-reader.py" "han-api.py" "watchdog.py")
SERVICE_DIR="/opt/hservice"
LOG_DIR="/var/log/hservice"

# Create necessary directories
sudo mkdir -p $SERVICE_DIR
sudo mkdir -p $LOG_DIR
sudo chown -R $SERVICE_USER:$SERVICE_USER $SERVICE_DIR
sudo chown -R $SERVICE_USER:$SERVICE_USER $LOG_DIR


# Generate systemd service files dynamically
for script in "${PYTHON_SCRIPTS[@]}"; do
    echo "Processing script: $script"
    SERVICE_NAME="${script%.py}"
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
 

    cat <<EOF | sudo tee $SERVICE_FILE > /dev/null
[Unit]
Description=Service for $script
After=network.target

[Service]
ExecStart=/usr/bin/python3 $SERVICE_DIR/$script
User=$SERVICE_USER
Group=$SERVICE_USER
Restart=always
StandardOutput=append:$LOG_DIR/${SERVICE_NAME}_\$(date +%d).log
StandardError=append:$LOG_DIR/${SERVICE_NAME}_\$(date +%d).log

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start the service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
done

echo "All services installed and running."

