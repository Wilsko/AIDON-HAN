#!/usr/bin/env python3
# Database report 
# 26.4.2026
# Reports record count, first timestamp, latest timestamp
#
import sqlite3
import os
from datetime import datetime

DBS = {
    "SENSOR": "/opt/hservice/sensor_data.db",
    "SENSOR HISTORY": "/opt/hservice/sensor_data_history.db",
    "SENSOR HISTORY 15 MIN": "/opt/hservice/sensor_data_15min.db",
    
}

def ts_to_str(ts):
    """Convert UNIX timestamp to readable format."""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return "INVALID"

def analyze_db(name, path):
    print(f"\n=== {name} ===")
    if not os.path.exists(path):
        print(f"Database missing: {path}")
        return

    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()

        # Count rows
        cur.execute("SELECT COUNT(*) FROM data")
        count = cur.fetchone()[0]

        if count == 0:
            print("Records: 0 (empty database)")
            return

        # First timestamp
        cur.execute("SELECT timestamp FROM data ORDER BY timestamp ASC LIMIT 1")
        first_ts = cur.fetchone()[0]

        # Latest timestamp
        cur.execute("SELECT timestamp FROM data ORDER BY timestamp DESC LIMIT 1")
        last_ts = cur.fetchone()[0]

        print(f"Records: {count}")
        print(f"First unix timestamp:  {first_ts} = {ts_to_str(first_ts)}")
        print(f"Latest unix timestamp: {last_ts} = {ts_to_str(last_ts)}")

    except Exception as e:
        print(f"ERROR reading {path}: {e}")
    finally:
        try:
            conn.close()
        except:
            pass


def main():
    print("HService Database Report")
    print("========================")
    for name, path in DBS.items():
        analyze_db(name, path)

if __name__ == "__main__":
    main()
