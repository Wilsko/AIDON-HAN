# WATCHDOG
# 18.4.2025 VP, Copilot
# reads latest timestamps in sensor, mgmt and gpio databasess
# and reports their age
# Notifications by mail may be added later
# 19.4.2025 set treshold and intervals literals. Corrected local time zone error
# 0.4 3.5.2025 added comments, text file name changed, edited exit info
import sqlite3
import time
from datetime import datetime
import pytz

# List of database files to check
DATABASES = [
    {"file": "sensor_data.db", "name": "Sensor Data"},
    {"file": "mgmt_data.db", "name": "Management Data"},
    {"file": "gpio_data.db", "name": "GPIO Data"}
]

REPORT_FILE = "watchdog.txt"
WRITE_MODE="w"
APPEND_MODE="a"
ALERT_TRESHOLD = 60
READ_INTERVAL = 30


def get_local_time():
    """
    Returns the current local time adjusted for the system's local timezone.
    """
    # Replace 'Europe/Helsinki' with your local timezone
    local_timezone = pytz.timezone("Europe/Helsinki")
    
    # Get current UTC time and convert to local time
    local_time = datetime.now(pytz.utc).astimezone(local_timezone)
    return local_time

def get_latest_timestamp(db_file):
    """
    Retrieves the latest timestamp from the database.

    Args:
        db_file (str): Path to the SQLite database file.

    Returns:
        int: The latest timestamp from the database, or None if no records exist.
    """
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row  # Enable row access by column name
    cursor = conn.cursor()

    try:
        # Query to fetch the latest timestamp
        cursor.execute("SELECT MAX(timestamp) FROM data")
        result = cursor.fetchone()
        if result and result[0] is not None:
            return int(result[0])
        return None  # No records exist
    except sqlite3.OperationalError as e:
        print(f"Error querying {db_file}: {e}")
        return None
    finally:
        conn.close()

def write_report(message, mode):
    """
    Writes the report message to the monitor.txt file.
    Overwriting of messages controlled by mode arg.
    Args:
        message (str): The message to write.
    """
    # Overwrite the report file with the latest data
    with open(REPORT_FILE, mode) as file:
        file.write(message + "\n")
    # Print the report to the console
    print(message)

def check_databases():
    """
    Checks each database and reports if the latest timestamp is more than one minute old.
    """
    current_time = int(time.time())
    alert_timestamp = current_time - ALERT_TRESHOLD  # look backwards

    # Get local time string for the report header
    loctime = get_local_time()
    local_time = loctime.strftime("%Y-%m-%d %H:%M:%S")
    report_lines = [f"--- Report Timestamp: {local_time} ---"]

    for db in DATABASES:
        latest_timestamp = get_latest_timestamp(db["file"])

        if latest_timestamp is None:
            report_lines.append(f"{db['name']}: No data found.")
        else:
            # Check if the timestamp is more than ALERT_TRESHOLD old
            if latest_timestamp < alert_timestamp:
                report_lines.append(f"{db['name']}: Latest timestamp is more than {ALERT_TRESHOLD} seconds old!")
            else:
                report_lines.append(f"{db['name']}: Latest timestamp is recent (within {ALERT_TRESHOLD} seconds).")

    # Combine all report lines into one string
    full_report = "\n".join(report_lines)
    write_report(message = full_report, mode = APPEND_MODE)

if __name__ == "__main__":
    print("Starting database monitoring...")
    try:
        while True:
            check_databases()
            time.sleep(READ_INTERVAL)  # Checking interval
    except KeyboardInterrupt:
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"--- Report Timestamp: {local_time} ---")
        report_lines = [f"--- Report Timestamp: {local_time} ---"]

        write_report(message = f"Program interrupted, mode = {APPEND_MODE} Exiting...", mode = APPEND_MODE)
