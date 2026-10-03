# SERIAL DATA READER
#
# reads  AIDON-HAN energy meter data from
# asus serial port ttyS0
# 31.10.2025 Initial version /VP

import serial
import re
import time
from datetime import datetime, timezone, timedelta

CUTOFF_TIME = 3660
SERIAL_PORT = "/dev/ttyS0"
SERIAL_BAUDRATE = 115200

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

def convert_timestamp_to_local_time(unix_timestamp):
    local_dt_object = datetime.fromtimestamp(unix_timestamp)
    return local_dt_object.strftime('%Y-%m-%d %H:%M:%S')
    
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

    # Parse the native datetime (without timezone info)
    native_datetime = datetime.strptime(timestamp_str, "%y%m%d%H%M%S")

    # Define fixed UTC+2 timezone
    utc_plus_2 = timezone(timedelta(hours=2))

    # Localize the native datetime to UTC+2
    localized_datetime = native_datetime.replace(tzinfo=utc_plus_2)

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
    Continuously reads serial data
	
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
            print(convert_timestamp_to_local_time(int(time.time())))
            print(line)
            print(stringData)
            # Read until line starting with "!" character
            while not stringData.startswith("!"):
                line = dataConnection.readline()
                stringData = line.decode('utf-8').strip()
                myList.append(stringData)

            # Process and store valid data
            parsed_data = parseData(myList)
            print(f"Timestamp: {parsed_data['timestamp']}, Valid data received")

        except Exception as e:
            print(f"Error processing serial data: {e}")

        # Pause for a moment to avoid flooding
        time.sleep(0.5)


def main():
    serport = serial.Serial(port="/dev/ttyS0", baudrate=115200)
    print("connected to sensor data serial port: " + serport.portstr)

    try:
        while True:
            # Read data from the serial port
            serial_data = readData(serport)
            timestamp = int(time.time())
            formatted_data = f"{serial_data}"
            print(f"{timestamp}, Data: {formatted_data}")

            # Wait for 10 seconds
            time.sleep(READ_INTERVAL)
    except KeyboardInterrupt:
        print("Program interrupted.")
    finally:
        serport.close()

if __name__ == "__main__":
    main()
