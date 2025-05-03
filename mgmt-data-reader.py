# MGMT DATA READER
# 17.4.2025 VP,Copilot
#
# Reads asus serial port ttyS4 and stores the input
# to mgmt_data database
# Reports the changes in switch state into mgmt_changes database
# 0.4 25.4.2025 Changes in screen output to include database name for clarify
#
import serial
import sqlite3
import time

DB_MAIN = "mgmt_data.db"
DB_CHANGES = "mgmt_changes.db"
MAX_RECORDS = 30
READ_INTERVAL = 10

def initialize_database(db_file):
    """Creates the 'data' table if it doesn't exist."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            timestamp INTEGER PRIMARY KEY,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()

def store_data(db_file, timestamp, data):
    """Stores timestamp and serial data in the specified database."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO data (timestamp, data) VALUES (?, ?)", (timestamp, data))
    conn.commit()
    conn.close()

def remove_old_records(db_file, max_records=None):
    """
    Removes records from the specified database.
    - If max_records is specified, ensures the table contains at most max_records entries.
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    if max_records:
        cursor.execute("SELECT COUNT(*) FROM data")
        record_count = cursor.fetchone()[0]
        print(f"Record count {record_count}")
        if record_count > max_records:
            # print("Max records reached, deleting old records")
            print(f"Deleting old records in {db_file}  ({record_count})")
            cursor.execute("""
                DELETE FROM data WHERE timestamp = (
                    SELECT MIN(timestamp) FROM data
                )
            """)
            conn.commit()
    conn.close()

def readManagement(mgmtConnection, previous_s_value=None):
    """Reads serial data from the management connection and processes it."""
    # Clear the input buffer
    mgmtConnection.reset_input_buffer()

    stringData = ""

    # Wait for line beginning with "S" character
    while not stringData.startswith("S"):
        try:
            line = mgmtConnection.readline()
            stringData = line.decode('utf-8').strip()
        except Exception as e:
            print(f"Garbage in serial port, skipping: {e}")

    s_value = stringData  # Value starting with "S"

    # Read next line, should be one starting with "T" character
    line = mgmtConnection.readline()
    stringData = line.decode('utf-8').strip()
    t_value = stringData  # Value starting with "T"

    # Compare 'S' value with previous and return data
    if s_value != previous_s_value:
        return [s_value, t_value, True]  # Change detected
    return [s_value, t_value, False]  # No change detected

def main():
    serMgmt = serial.Serial(port="/dev/ttyS4", baudrate=300)
    print("connected to management: " + serMgmt.portstr)

    # Initialize the databases
    initialize_database(DB_MAIN)
    initialize_database(DB_CHANGES)

    previous_s_value = None  # Track last "S" value

    try:
        while True:
            # Read data from the serial port
            serial_data, t_value, change_detected = readManagement(serMgmt, previous_s_value)

            # Update "S" value tracker
            previous_s_value = serial_data

            # Prepare the data for storage
            timestamp = int(time.time())
            formatted_data = f"{serial_data}, {t_value}"

            # Store data in the main database
            store_data(DB_MAIN, timestamp, formatted_data)
            print(f"Data Stored in {DB_MAIN} - Timestamp: {timestamp}, Data: {formatted_data}")

            # Remove old records from the main database
            remove_old_records(DB_MAIN, max_records=MAX_RECORDS)

            # If "S" value has changed, store in the changes database
            if change_detected:
                store_data(DB_CHANGES, timestamp, formatted_data)
                print(f"Data Stored in {DB_CHANGES} - Timestamp: {timestamp}, Data: {formatted_data}")

                # Ensure changes database does not exceed 30 records
                remove_old_records(DB_CHANGES, max_records=MAX_RECORDS)

            # Wait for 10 seconds
            time.sleep(READ_INTERVAL)
    except KeyboardInterrupt:
        print("Program interrupted.")
    finally:
        serMgmt.close()

if __name__ == "__main__":
    main()
