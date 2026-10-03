#!/usr/bin/env python3
# Total energy data reader from sensor_data database
# 27.4.2026 VP, Copilot

#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

DB_FILE = "./sensor_data.db"

def safe_human_time(ts):
    """Convert UNIX timestamp → human readable, safely."""
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "INVALID_TIMESTAMP"

def extract_total_energy_value(json_text):
    """
    Extract the numeric 'value' from JSON key '1-0:1.8.0'.
    Returns None if missing or malformed.
    """
    try:
        items = json.loads(json_text)
        for entry in items:
            if entry["key"] == "1-0:1.8.0":
                return entry["value"]
        return None
    except Exception:
        return None

def main():
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
    except Exception as e:
        print(f"ERROR: Cannot open database: {e}")
        return

    try:
        cur.execute("SELECT timestamp, sensor_data FROM data ORDER BY timestamp ASC")
    except Exception as e:
        print(f"ERROR: Query failed: {e}")
        return

    rows = cur.fetchall()
    if not rows:
        print("No records found.")
        return

    for ts, data_json in rows:
        human = safe_human_time(ts)
        total_energy_value = extract_total_energy_value(data_json)

        print(f"{human}, {total_energy_value}")
        
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
    print(f"First timestamp: {safe_human_time(first_ts)}")
    print(f"Latest timestamp: {safe_human_time(last_ts)}")


    conn.close()

if __name__ == "__main__":
    main()
