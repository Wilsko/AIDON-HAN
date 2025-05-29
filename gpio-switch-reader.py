# GPIO-SWITCH-READER
# 8.4.2025 VP, Copilot
# Reads GPIO pin 33 and stores the result in sqlite3 database
# gpio_data. It also stores the result into gpio_changes database
# when pin 33 state change is detected.
# When pin state is HIGH, the value stored is 0, 1 otherwise.
# Stored value means closed switch.
# Record count of both databases is limited to MAX_RECORDS, Oldest 
# records are deleted when necessary.
# Interval between GPIO reads is defined as READ_INTERVAL
# Program is ment to be tun as a service process
# 0.8 26.4.2025 Changes in screen output to include database name for clarify

import ASUS.GPIO as GPIO
import sqlite3
import time

DB_MAIN = "gpio_data.db"
DB_CHANGES = "gpio_changes.db"
PIN_NUMBER = 33
MAX_RECORDS = 30
READ_INTERVAL = 10

# GPIO setup

GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
GPIO.setup(PIN_NUMBER, GPIO.IN)  # Set pin 33 as an input

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def initialize_database(db_file):
    """Creates the 'data' table if it doesn't exist."""
    conn = create_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            timestamp INTEGER PRIMARY KEY,
            Switch2 TEXT
        )
    """)
    conn.commit()
    conn.close()

def store_data(db_file, timestamp, switch_state):
    """Stores timestamp and GPIO state in the specified database."""
    conn = create_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO data (timestamp, Switch2) VALUES (?, ?)", (timestamp, switch_state))
    conn.commit()
    conn.close()

def remove_old_records(db_file, max_records=None):
    """
    Removes records from the specified database.
    - If max_records is specified, ensures the table contains at most max_records entries.
    """
    conn = create_connection(db_file)
    cursor = conn.cursor()

    if max_records:
        cursor.execute("SELECT COUNT(*) FROM data")
        record_count = cursor.fetchone()[0]
        if record_count > max_records:
            print(f"Max records reached, deleting old records in {db_file}, record count = {record_count}")
            cursor.execute("""
                DELETE FROM data WHERE timestamp = (
                    SELECT MIN(timestamp) FROM data
                )
            """)
            conn.commit()
    conn.close()

def read_and_store_gpio():
    """Reads GPIO pin 33 and stores the state in the main database."""
    previous_pin_state = None  # Tracks the last pin state

    while True:
        # Read pin state
        pin_state = GPIO.input(PIN_NUMBER)

        # Map pin state to 'Switch2' field
        switch_state = "0" if pin_state == GPIO.HIGH else "1"

        # Get current time as Unix epoch time
        timestamp = int(time.time())

        # Store data in the main database
        store_data(DB_MAIN, timestamp, switch_state)
        print(f"Data Stored in {DB_MAIN} - Timestamp: {timestamp}, Switch2: {switch_state}")

        # Remove old records from the main database
        remove_old_records(DB_MAIN, max_records=MAX_RECORDS)

        # If the pin state has changed, store data in the changes database
        if switch_state != previous_pin_state:
            store_data(DB_CHANGES, timestamp, switch_state)
            print(f"Data Stored in {DB_CHANGES} - Timestamp: {timestamp}, Switch2: {switch_state}")

            # Ensure changes database does not exceed MAX_RECORDS records
            remove_old_records(DB_CHANGES, max_records=MAX_RECORDS)

        # Update previous state
        previous_pin_state = switch_state

        # Wait for READ_INTERVAL seconds
        time.sleep(READ_INTERVAL)

if __name__ == "__main__":
    # Display database name and GPIO port number at startup
    print(f"Main Database Name: {DB_MAIN}")
    print(f"Changes Database Name: {DB_CHANGES}")
    print(f"GPIO Port Number: {PIN_NUMBER}")

    # Initialize the databases
    initialize_database(DB_MAIN)
    initialize_database(DB_CHANGES)

    try:
        read_and_store_gpio()
    except KeyboardInterrupt:
        print("Program interrupted.")
    finally:
        GPIO.cleanup()  # Clean up GPIO settings

