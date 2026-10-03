#!/usr/bin/env python3
# db records
# prints database records
# sensor data: timestamp, total energy
# other db's: timastamp, data
# 26.4.2026 VP
#
import sqlite3
import json
from datetime import datetime
import argparse

DBS = [
    ("/opt/hservice/sensor_data.db", "LIVE SENSOR DATA"),
    ("/opt/hservice/sensor_data_15min.db", "15-MIN HISTORY"),
    ("/opt/hservice/sensor_data_history.db", "HOURLY HISTORY")
]

def human_time(ts):
    try:
        return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M:%S")
    except:
        return "INVALID_TIMESTAMP"

def extract_from_sensor_data(json_text):
    """
    sensor_data.db format:
    JSON string containing a list of dicts:
    [
      {"key": "1-0:1.8.0", "value": 25240.932, "unit": "kWh"},
      ...
    ]
    """
    try:
        items = json.loads(json_text)
        if not isinstance(items, list):
            return None

        for entry in items:
            if entry.get("key") == "1-0:1.8.0":
                return entry.get("value")
    except:
        pass

    return None

def report_header(label, path, count, first_ts, last_ts):
    print(f"\n=== {label}: {path} ===")
    print(f"Records: {count}")
    print(f"First timestamp: {first_ts} ({human_time(first_ts)})" if first_ts else "First timestamp: None")
    print(f"Last timestamp:  {last_ts} ({human_time(last_ts)})" if last_ts else "Last timestamp: None")
    print("-" * 60)

def process_sensor_data_db(path, label):
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("SELECT timestamp, sensor_data FROM data ORDER BY timestamp ASC")
    rows = cur.fetchall()

    if not rows:
        report_header(label, path, 0, None, None)
        return

    count = len(rows)
    first_ts = rows[0][0]
    last_ts = rows[-1][0]

    report_header(label, path, count, first_ts, last_ts)

    for ts, sensor_json in rows:
        total_energy = extract_from_sensor_data(sensor_json)
        print(f"{human_time(ts)}  total_energy={total_energy}")

    report_header(label, path, count, first_ts, last_ts)

    conn.close()

def process_15min_db(path, label):
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("SELECT timestamp, total_energy, consumed_energy FROM data ORDER BY timestamp ASC")
    rows = cur.fetchall()

    if not rows:
        report_header(label, path, 0, None, None)
        return

    count = len(rows)
    first_ts = rows[0][0]
    last_ts = rows[-1][0]


    report_header(label, path, count, first_ts, last_ts)

    for ts, total_energy, consumed_energy in rows:
        print(f"{human_time(ts)}  total_energy={total_energy}  consumed={consumed_energy}")

    report_header(label, path, count, first_ts, last_ts)

    conn.close()

def process_history_db(path, label):
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("SELECT timestamp, total_energy FROM data ORDER BY timestamp ASC")
    rows = cur.fetchall()

    if not rows:
        report_header(label, path, 0, None, None)
        return

    count = len(rows)
    first_ts = rows[0][0]
    last_ts = rows[-1][0]

    report_header(label, path, count, first_ts, last_ts)    

    for ts, total_energy in rows:
        print(f"{human_time(ts)}  total_energy={total_energy}")

    report_header(label, path, count, first_ts, last_ts)

    conn.close()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=False, help="Required parameter --db sets Database: 15, 60 or sensor.")
    args = parser.parse_args()
    if args.db == "sensor":
        process_sensor_data_db(DBS[0][0], DBS[0][1])
    if args.db == "15":
        process_15min_db(DBS[1][0], DBS[1][1])
    if args.db == "60":
        process_history_db(DBS[2][0], DBS[2][1])
    if args.db == None:
        process_sensor_data_db(DBS[0][0], DBS[0][1])
        print("Parameter --db sets Database to analyze: 15, 60 or sensor (default).")

if __name__ == "__main__":
    main()
