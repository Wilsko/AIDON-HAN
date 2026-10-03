# Check 15 mimutes database for anomalities ie.
# timestamps too close or missing records.
# 28.4.2026 VP
#

from datetime import datetime
import sqlite3, time

HISTORY_15MIN_DB_FILE = "/opt/hservice/sensor_data_15min.db"

def sanity_check_last_24h(max_expected=10.0):
    conn = sqlite3.connect(HISTORY_15MIN_DB_FILE)
    cursor = conn.cursor()
    cutoff_time = int(time.time()) - 24*3600
    cursor.execute("""
        SELECT timestamp, total_energy, consumed_energy
        FROM data
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
    """, (cutoff_time,))
    rows = cursor.fetchall()
    conn.close()

    print("timestamp | local time | total_energy | consumed_energy | status")
    print("-"*80)

    anomalies = {"MISSING":0, "NEGATIVE":0, "HIGH":0, "TOO_CLOSE":0}
    prev_ts = None

    for ts, total, consumed in rows:
        local = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M:%S")
        status = "OK"
        if consumed is None:
            status = "MISSING"
            anomalies["MISSING"] += 1
        elif consumed < 0:
            status = "NEGATIVE"
            anomalies["NEGATIVE"] += 1
        elif consumed > max_expected:
            status = f"HIGH>{max_expected}"
            anomalies["HIGH"] += 1
        if prev_ts is not None and (ts - prev_ts) < 15*60:
            status += " TOO_CLOSE"
            anomalies["TOO_CLOSE"] += 1
        prev_ts = ts
        print("{:<12} | {:<16} | {:<12.3f} | {:<14} | {}".format(
            ts, local, total, consumed, status
        ))

    print("\nSummary of anomalies:")
    for key, count in anomalies.items():
        print(f"{key}: {count}")
    print(f"Total rows checked: {len(rows)}")

sanity_check_last_24h()