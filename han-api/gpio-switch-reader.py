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
# Program is ment to be run as a service process
# 0.8 26.4.2025 Changes in screen output to include database name for clarify
# 0.9 4.3.2026 Alert/Warning mails 
# 1.0 4.3.2026 S1 and S2 Names
# 1.1 10.4.2026 Version info
# 1.2 19.4.2026 mail enable implemented, safe alertmail.config read
# 1.3 12.5.2026  Corrected s2 alert texts
#                S2: 0 HAN System: Kotelon ovi kiinni
#                S2: 1 HAN System Alert: Kotelon ovi auki
#                HAN System: Switch 2 (GPIO port) change detected 
#
# 1.4 12.8.2026 Delayed start after gpio setup
# 1.5 29.8.2026 Improved error handling in main()
#
# version info 0.1.5

VERSION="0.1.5"

import time
import sys
if "--version" in sys.argv:
    print(VERSION)
    sys.exit(0)



import ASUS.GPIO as GPIO
import sqlite3
from datetime import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
import platform
import os

NEWLINE='\n'

READ_INTERVAL = 10
DB_MAIN = "gpio_data.db"
DB_CHANGES = "gpio_changes.db"
PIN_NUMBER = 33
MAX_RECORDS = 30
READ_INTERVAL = 10
VALID_PORTS = {"465", "587"}   # SSL/TLS or STARTTLS


# GPIO setup

GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
GPIO.setup(PIN_NUMBER, GPIO.IN)  # Set pin 33 as an input

# Start delay: Wait for 10 seconds
START_DELAY=5
print(f"{__file__} version {VERSION} -- Delayed start ...")
time.sleep(START_DELAY)
print(f"{__file__} version {VERSION} starting")


def load_mail_config(filename="alertmail.config"):
    """
    Safely load and validate alert mail configuration.
    Returns a dict with typed values or raises ValueError with a clear message.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Config file not found: {filename}")

    raw = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"Invalid config line (missing '='): {line}")
            key, value = line.split("=", 1)
            raw[key.strip()] = value.strip()

    # Required string fields
    required_keys = ["server", "port", "from_addr", "password", "to_addr",
                     "pcb_hot", "hysteresis", "cpu_hot", "enabled"]

    for key in required_keys:
        if key not in raw:
            raise ValueError(f"Missing required config key: {key}")

    # Validate port
    port = raw["port"]
    if port not in VALID_PORTS:
        raise ValueError(f"Invalid port '{port}'. Must be one of: {', '.join(VALID_PORTS)}")

    # Convert numeric fields
    pcb_hot = safe_str_to_int(raw["pcb_hot"])
    hysteresis = safe_str_to_int(raw["hysteresis"])
    cpu_hot = safe_str_to_int(raw["cpu_hot"])
    enabled = safe_str_to_int(raw["enabled"])

    if pcb_hot is None or hysteresis is None or cpu_hot is None:
        raise ValueError("Numeric fields pcb_hot, hysteresis, cpu_hot must be valid integers.")


    # Return typed config
    return {
        "enabled": enabled,
        "server": raw["server"],
        "port": port,
        "from_addr": raw["from_addr"],
        "password": raw["password"],
        "to_addr": raw["to_addr"],
        "pcb_hot": pcb_hot,
        "hysteresis": hysteresis,
        "cpu_hot": cpu_hot,
    }



def send_alert(subject, body):
    cfg = load_mail_config()
#    print(cfg)
    
    servername=cfg["server"]
    port=cfg["port"]
    from_addr=cfg["from_addr"]
    password=cfg["password"]
    to_addr=cfg["to_addr"]
    stamp=get_local_time()
    date_time = stamp.strftime("%d.%m.%Y  %H:%M:%S")
    host=platform.node()
    message = host+NEWLINE+date_time+NEWLINE+body 
    #    message=body
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    print(f"From: {from_addr}, To: {to_addr}")
    print(f"mail enabled = {cfg['enabled']}")    
    if cfg["enabled"] == 1:
        with smtplib.SMTP_SSL(servername, port, timeout=10) as server:
            server.set_debuglevel(0)
            server.login(from_addr, password)
            server.send_message(msg)
# String to integer conversion in Python

def safe_str_to_int(s: str, base: int = 10) -> int:
    """
    Convert a string to an integer safely.
    
    :param s: The string to convert.
    :param base: The numeric base (default is 10).
    :return: The integer value.
    :raises ValueError: If the string is not a valid integer.
    :
    :returns zero on errors
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string.")
        return 0
    
    s = s.strip()  # Remove leading/trailing spaces
    
    if s == "":
        raise ValueError("Empty string cannot be converted to integer.")
        return 0
    try:
        return int(s, base)
    except ValueError:
        raise ValueError(f"'{s}' is not a valid integer in base {base}.")
       
        return 0

def get_local_time():
    """
    Returns the current local time adjusted for the system's local timezone.
    """
    # Replace 'Europe/Helsinki' with your local timezone
    local_timezone = pytz.timezone("Europe/Helsinki")

    # Get current UTC time and convert to local time
    local_time = datetime.now(pytz.utc).astimezone(local_timezone)
    return local_time

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
        dt = datetime.fromtimestamp(timestamp)   # local time
        strtime = dt.strftime("%Y-%m-%d %H:%M:%S")
        # Store data in the main database
        store_data(DB_MAIN, timestamp, switch_state)
        print(f"Data Stored in {DB_MAIN} - Timestamp: {timestamp}, Switch2: {switch_state}")

        # Remove old records from the main database
        remove_old_records(DB_MAIN, max_records=MAX_RECORDS)

        # If the pin state has changed, store data in the changes database
        if switch_state != previous_pin_state:
            store_data(DB_CHANGES, timestamp, switch_state)
            print(f"Data Stored in {DB_CHANGES} - Timestamp: {timestamp}, Switch2: {switch_state}")
            print(f"HAN System: Switch 2 (GPIO) change detected ------- Switch 2: {switch_state}")
            if switch_state == "0":
                send_alert("HAN System Alert: Kotelon ovi kiinni",f"GPIO Data S2: {switch_state}")
            else:
                send_alert("HAN System: Kotelon ovi auki",f"GPIO Data S2: {switch_state}")
            # Ensure changes database does not exceed MAX_RECORDS records
            remove_old_records(DB_CHANGES, max_records=MAX_RECORDS)

        # Update previous state
        previous_pin_state = switch_state

        # Wait for READ_INTERVAL seconds
        time.sleep(READ_INTERVAL)

import traceback

def main():
    # Display database name and GPIO port number at startup
    print(f"Main Database Name: {DB_MAIN}")
    print(f"Changes Database Name: {DB_CHANGES}")
    print(f"GPIO Port Number: {PIN_NUMBER}")

    # Initialize the databases
    initialize_database(DB_MAIN)
    initialize_database(DB_CHANGES)

	
    while True:
        try:
            read_and_store_gpio()   # your function
        except KeyboardInterrupt:
            print("Program interrupted by user.")
            break
        except Exception as e:
            print(f"read_and_store_gpio() failed: {e}")
            traceback.print_exc()
            time.sleep(1)  # wait before retry
        else:
            # Optional: if your function is supposed to loop internally,
            # you can sleep here instead.
            time.sleep(0.1)

    GPIO.cleanup()
    print("GPIO cleaned up.")

if __name__ == "__main__":
    main()

	
