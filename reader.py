import serial
import re
from datetime import datetime, timezone, timedelta
import sqlite3
import json

def readData(dataConnection):
    # clear the input buffer
    dataConnection.reset_input_buffer()

    myList = []
    stringData = ""
    
    # wait for line beginning with "/ADN9" character
    while not stringData.startswith("/ADN9"):
        try:
            line = dataConnection.readline()
            stringData = line.decode('utf-8').strip()
        except:
            print("Garbage in serial port, skipping")
    myList.append(stringData)
    
    # read until line starting with "!" character
    while not stringData.startswith("!"):
        line = dataConnection.readline()
        stringData = line.decode('utf-8').strip()
        myList.append(stringData)

    return myList

def parseData(inputList):
    data = {"values": []}
    for input in inputList:
        if input.startswith("0-0:1.0.0"):
            data["timestamp"] = parseTimestamp(input)
        elif input.startswith("1-0:"):
            data["values"].append(parseValue(input))
    return data

def parseTimestamp(input):
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
    match = re.match(r"(.+)\(([\d\.]+)\*([^\)]+)\)", input)
    if match:
        return {
            "key": match.group(1),
            "value": float(match.group(2)),  # Convert the number to a float
            "unit": match.group(3)
        }
    else:
        raise ValueError("Input string does not match the expected format.")
    
def writeData(input):
    # Connect to SQLite
    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")

    # Create a table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data (
            timestamp INTEGER PRIMARY KEY,
            sensor_data TEXT
        )
    ''')

    cursor.execute("INSERT INTO data (timestamp, sensor_data) VALUES (?, ?)",
                   (input["timestamp"], json.dumps(input["values"])))
    
    conn.commit()
    conn.close()

serData = serial.Serial(
        port = "/dev/ttyS0", baudrate = 115200
)

print("connected to data: " + serData.portstr)
dataAsList = readData(serData)
dataAsDict = parseData(dataAsList)
writeData(dataAsDict)

serData.close()
