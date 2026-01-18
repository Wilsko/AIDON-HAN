# SENSOR DATA READER
#
# Reads AIDON-HAN energy meter data from serial port, for!mats the input data
# to JSON compatible list and stores the result to sensor_data sqlite3 database.
#
# Extended: 15-min history DB with consumed energy, 31-day retention,
# query helpers for last 24h and daily totals, and plotting helpers.
# 10.12.2025 Added Graphs png tile output.  24h graph type changed to bar. 
# 11.12.2025 x-akselin aikamerkit
# 16.12.2025 poistettu plot-funktioiden kutsut. Tehdään vain 15-min kannan kirjoitus.
#            koodataan graafeille oma ohjelma jos tarvis
# 21.12.2025 3 desimaalia consumed-energyyn 
# 16.1.2026  CUTOFF_TIME = 2*3660
import serial
import re
import sqlite3
import json
import time
from datetime import datetime, timezone, timedelta

import matplotlib
matplotlib.use('Agg')   # Use non-GUI backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# CUTOFF_TIME = 3660
CUTOFF_TIME = 2*3660

DB_FILE = "sensor_data.db"
HISTORY_DB_FILE = "sensor_data_history.db"
HISTORY_15MIN_DB_FILE = "sensor_data_15min.db"
SERIAL_PORT = "/dev/ttyS0"
SERIAL_BAUDRATE = 115200
LAST_HISTORY_WRITE_MINUTE = -1
LAST_TOTAL_ENERGY = None
HISTORY_WRITE_MINUTES = [0, 15, 30, 45]

def convert_timestamp_to_local_time(unix_timestamp):
    local_dt_object = datetime.fromtimestamp(unix_timestamp)
    return local_dt_object.strftime('%Y-%m-%d %H:%M:%S')

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def initialize_database():
    # History DB (total energy at 15-min marks)
    history_conn = create_connection(HISTORY_DB_FILE)
    history_cursor = history_conn.cursor()
    history_cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            timestamp INTEGER PRIMARY KEY,
            total_energy REAL
        )
    """)
    history_conn.commit()
    history_conn.close()

    # Sensor data DB (raw parsed payloads)
    conn = create_connection(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            timestamp INTEGER PRIMARY KEY,
            sensor_data TEXT
        )
    """)
    conn.commit()
    conn.close()

    # 15-min history DB (total + consumed delta)
    history15_conn = create_connection(HISTORY_15MIN_DB_FILE)
    history15_cursor = history15_conn.cursor()
    history15_cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            timestamp INTEGER PRIMARY KEY,
            total_energy REAL,
            consumed_energy REAL
        )
    """)
    history15_conn.commit()
    history15_conn.close()

def remove_old_records():
    cutoff_time = int(time.time()) - CUTOFF_TIME
    cutoff_str = convert_timestamp_to_local_time(cutoff_time)
    conn = create_connection(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM data")
    record_count = cursor.fetchone()[0]
    print(f"Record count {record_count}")
    print(f"{DB_FILE}: Deleting old records. Cutoff timestamp = {cutoff_str} ({cutoff_time})")
    cursor.execute("DELETE FROM data WHERE timestamp < ?", (cutoff_time,))
    conn.commit()
    conn.close()

def remove_old_15min_records():
    """Remove records older than 31 days from sensor_data_15min.db."""
    cutoff_time = int(time.time()) - (31 * 24 * 3600)
    conn = create_connection(HISTORY_15MIN_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM data WHERE timestamp < ?", (cutoff_time,))
    conn.commit()
    conn.close()

def init_last_total_energy_from_db():
    """Initialize LAST_TOTAL_ENERGY from the most recent 15-min record if available."""
    global LAST_TOTAL_ENERGY
    conn = create_connection(HISTORY_15MIN_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT total_energy FROM data ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row is not None:
        LAST_TOTAL_ENERGY = row[0]

def writeData(input):
    global LAST_HISTORY_WRITE_MINUTE, LAST_TOTAL_ENERGY

    remove_old_records()

    # Insert into sensor_data.db
    conn = create_connection(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO data (timestamp, sensor_data) VALUES (?, ?)",
                   (input["timestamp"], json.dumps(input["values"])))
    conn.commit()
    conn.close()

    # Extract total energy (kWh) from values
    totalEnergy = next((item for item in input["values"] if item["key"] == "1-0:1.8.0"), None)
    if totalEnergy:
        ts_dt = datetime.fromtimestamp(input["timestamp"])
        if ts_dt.minute in HISTORY_WRITE_MINUTES and ts_dt.minute != LAST_HISTORY_WRITE_MINUTE:
            # Write to simple history DB
            hconn = create_connection(HISTORY_DB_FILE)
            hcur = hconn.cursor()
            hcur.execute("INSERT INTO data (timestamp, total_energy) VALUES (?, ?)",
                         (input["timestamp"], totalEnergy["value"]))
            hconn.commit()
            hconn.close()

            # Prepare consumed delta for 15-min DB
            if LAST_TOTAL_ENERGY is None:
                # Try to initialize from DB in case of restart
                init_last_total_energy_from_db()
            consumed_energy = None
            if LAST_TOTAL_ENERGY is not None:
                consumed_energy = round(totalEnergy["value"] - LAST_TOTAL_ENERGY,3)
                # Guard against negative due to meter resets/rollovers
                if consumed_energy < 0:
                    consumed_energy = None

            # Write to 15-min DB
            h15conn = create_connection(HISTORY_15MIN_DB_FILE)
            h15cur = h15conn.cursor()
            h15cur.execute(
                "INSERT INTO data (timestamp, total_energy, consumed_energy) VALUES (?, ?, ?)",
                (input["timestamp"], totalEnergy["value"], consumed_energy)
            )
            h15conn.commit()
            h15conn.close()

            # Cleanup retention
            remove_old_15min_records()

            # Update trackers
            LAST_TOTAL_ENERGY = totalEnergy["value"]
            LAST_HISTORY_WRITE_MINUTE = ts_dt.minute

def parseData(inputList):
    data = {"values": []}
    for line in inputList:
        if line.startswith("0-0:1.0.0"):
            data["timestamp"] = parseTimestamp(line)
        elif line.startswith("1-0:"):
            data["values"].append(parseValue(line))
    return data

def parseTimestamp(line):
    match = re.search(r"\((\d+[SW])\)", line)
    if match:
        timestamp_str = match.group(1)[:-1]  # strip trailing S/W
    else:
        raise ValueError("No timestamp found in the input string.")
    naive_datetime = datetime.strptime(timestamp_str, "%y%m%d%H%M%S")
    utc_plus_2 = timezone(timedelta(hours=2))
    localized_datetime = naive_datetime.replace(tzinfo=utc_plus_2)
    utc_datetime = localized_datetime.astimezone(timezone.utc)
    return int(utc_datetime.timestamp())

def parseValue(line):
    match = re.match(r"(.+)\(([\d\.]+)\*([^\)]+)\)", line)
    if match:
        return {
            "key": match.group(1),
            "value": float(match.group(2)),
            "unit": match.group(3)
        }
    else:
        raise ValueError("Input string does not match the expected format.")

def readData(dataConnection):
    dataConnection.reset_input_buffer()
    while True:
        try:
            frames = []
            s = ""
            # Wait for header line beginning with "/ADN9"
            while not s.startswith("/ADN9"):
                line = dataConnection.readline()
                s = line.decode('utf-8').strip()
            frames.append(s)
            # Continue until "!" line
            while not s.startswith("!"):
                line = dataConnection.readline()
                s = line.decode('utf-8').strip()
                frames.append(s)

            parsed_data = parseData(frames)
            writeData(parsed_data)
            print(f"Timestamp: {parsed_data['timestamp']}, Valid data received for {DB_FILE}")

        except Exception as e:
            print(f"Error processing serial data: {e}")

        time.sleep(0.5)


# ------------------ Main ------------------

if __name__ == "__main__":
    # Initialize DBs
    initialize_database()
    # Initialize delta baseline from DB (helps after restarts)
    init_last_total_energy_from_db()

    # Open serial and start reading
    serData = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUDRATE)
    print("Connected to serial port: " + serData.portstr)

    try:
        readData(serData)
    except KeyboardInterrupt:

        print("Program interrupted. Exiting...")
    finally:
        serData.close()
