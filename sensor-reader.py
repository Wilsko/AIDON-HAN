# SENSOR DATA READER
# 
# Reads AIDON-HAN energy meter data from
# asus serial port ttyS4, formats the input data
# to json compaltible list and stores the result
# to sensor_data sqlite3 database
# 
# 18.4.2025 Modified from reader.py VP, Copilot
# 0.3 25.4.2025 Comments added
# 0.4 25.4.2025 Changes in screen output to include database name for clarify
# 0.5 3.5.2025 Added comments, changed serial port parameters as literals
#              Screen output changes in remove_old_files()

import serial
import re
import sqlite3
import json
import time
from datetime import datetime, timezone, timedelta
CUTOFF_TIME = 3660

DB_FILE = "sensor_data.db"
SERIAL_PORT = "/dev/ttyS0"
SERIAL_BAUDRATE = 115200

def convert_timestamp_to_local_time(unix_timestamp):
    """
    Converts a Unix integer timestamp to a human-readable local date and time string.

    Args:
        unix_timestamp (int): Unix timestamp (seconds since epoch).

    Returns:
        str: Date and time in the local time zone in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    # Convert Unix timestamp to a local datetime object
    local_dt_object = datetime.fromtimestamp(unix_timestamp)
    
    # Format the local datetime object as a string
    formatted_time = local_dt_object.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time

def initialize_database():
    """
    Creates the 'data' table in the sensor_data.db database if it doesn't exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            timestamp INTEGER PRIMARY KEY,
            sensor_data TEXT
        )
    """)
    conn.commit()
    conn.close()
    
def remove_old_records():
    """Removes records that are more than one hour and one minute old."""
    # Calculate the cutoff time (current time minus 1 hour and 1 minute)
    # 
   
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM data")
    record_count = cursor.fetchone()[0]
    cutoff_time = int(time.time()) - CUTOFF_TIME  # 3600 seconds + 60 seconds
    cutoff_str = convert_timestamp_to_local_time(cutoff_time)

    print(f"Record count {record_count}")
    print(f"{DB_FILE}: Deleting old records. Cutoff timestamp = {cutoff_str} ({cutoff_time})")
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM data WHERE timestamp < ?", (cutoff_time,))
    conn.commit()
    conn.close()
    # print(f"Old records older than 1 hour and 1 minute have been removed.")       

def writeData(input):
    """
    Stores formatted data into the SQLite sensor_data.db database.

    Args:
        input (dict): A dictionary containing timestamp and sensor data.
    """
    
    # Remove old records first
    remove_old_records()
    
    # Add new data
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")

    cursor.execute("INSERT INTO data (timestamp, sensor_data) VALUES (?, ?)",
                   (input["timestamp"], json.dumps(input["values"])))

    conn.commit()
    conn.close()

def parseData(inputList):
    """
    Parses the serial data into a structured dictionary.

    Args:
        inputList (list): List of lines read from the serial port.

    Returns:
        dict: Dictionary containing parsed timestamp and values.
    """
    data = {"values": []}
    for input in inputList:
        if input.startswith("0-0:1.0.0"):
            data["timestamp"] = parseTimestamp(input)
        elif input.startswith("1-0:"):
            data["values"].append(parseValue(input))
    return data

def parseTimestamp(input):
    """
    Extracts the timestamp from the serial data.

    Args:
        input (str): A line of serial data containing the timestamp.

    Returns:
        int: The Unix epoch time for the extracted timestamp.
    """
    match = re.search(r"\((\d+S)\)", input)
    if match:
        timestamp_str = match.group(1)[:-1]  # Remove the trailing "S"
    else:
        raise ValueError("No timestamp found in the input string.")

    # Parse the naive datetime (without timezone info)
    naive_datetime = datetime.strptime(timestamp_str, "%y%m%d%H%M%S")

    # Define fixed UTC+2 timezone
    utc_plus_2 = timezone(timedelta(hours=2))

    # Localize the naive datetime to UTC+2
    localized_datetime = naive_datetime.replace(tzinfo=utc_plus_2)

    # Convert to UTC for epoch conversion
    utc_datetime = localized_datetime.astimezone(timezone.utc)

    return int(utc_datetime.timestamp())

def parseValue(input):
    """
    Extracts key-value pairs from the serial data.

    Args:
        input (str): A line of serial data.

    Returns:
        dict: A dictionary containing key, value, and unit.
    """
    match = re.match(r"(.+)\(([\d\.]+)\*([^\)]+)\)", input)
    if match:
        return {
            "key": match.group(1),
            "value": float(match.group(2)),  # Convert the number to a float
            "unit": match.group(3)
        }
    else:
        raise ValueError("Input string does not match the expected format.")
        

def readData(dataConnection):
    """
    Continuously reads serial data and processes it into sensor_data.db.

    Args:
        dataConnection: The serial connection object.
    """
    dataConnection.reset_input_buffer()  # Clear the input buffer

    while True:
        try:
            myList = []
            stringData = ""

            # Wait for line beginning with "/ADN9" character
            while not stringData.startswith("/ADN9"):
                line = dataConnection.readline()
                stringData = line.decode('utf-8').strip()

            myList.append(stringData)

            # Read until line starting with "!" character
            while not stringData.startswith("!"):
                line = dataConnection.readline()
                stringData = line.decode('utf-8').strip()
                myList.append(stringData)

            # Process and store valid data
            parsed_data = parseData(myList)
            writeData(parsed_data)
            print(f"Timestamp: {parsed_data['timestamp']}, Valid data received for {DB_FILE}")

        except Exception as e:
            print(f"Error processing serial data: {e}")

        # Pause for a moment to avoid flooding
        time.sleep(0.5)

if __name__ == "__main__":
    # Initialize the database
    initialize_database()

    # Set up the serial connection
    serData = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUDRATE)
    print("Connected to serial port: " + serData.portstr)

    try:
        # Start continuously reading and processing data
        readData(serData)
    except KeyboardInterrupt:
        print("Program interrupted. Exiting...")
    finally:
        serData.close()
