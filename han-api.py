# HAN API
# 18.4.2025 VP, with a little help from my friend, Copilot
#
# Publishes http apis:
# sensor_data
# mgmt_data
# gpio_data
# mgmt_changes
# gpio_changes
# monitor
#
# 0.7 25.4.2025  sensor_data: Order by timestamp desc
# 0.7 3.5.2025 changed MONITOR_FILE = "watchdog.txt"
# 0.8 19.12.2025 Added count parameter to api sqlite3 based functions.
#                If parameter exists, return count number of records, otherwise return all
# 0.9 15.1.2026  Changed fetch_all_data function name to fetch_db_data
#                Added api functions get_sensor_15min_data(), get_sensor_hourly_data()
#
from flask import Flask, jsonify, request
from flask_cors import CORS
# CORS was needed for security compatibility when nginx is not in use
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # Allow all origins for simplicity
# Database file paths

# Database file paths
SENSOR_DB = "sensor_data.db"
HISTORY_HOURLY_DB = "sensor_data_history.db"
HISTORY_15MIN_DB = "sensor_data_15min.db"
MGMT_DB = "mgmt_data.db"
GPIO_DB = "gpio_data.db"
MGMT_CHANGES_DB = "mgmt_changes.db"
GPIO_CHANGES_DB = "gpio_changes.db"

MONITOR_FILE = "watchdog.txt"

# Define a maximum cap for records returned
MAX_RECORDS = 1000

def fetch_db_data(db_file, base_query, count=None):
    """
    Fetch rows from the specified database using the provided query.
    Optionally limit the number of rows returned.

    Args:
        db_file (str): Path to the SQLite database file.
        base_query (str): SQL query to execute (without LIMIT).
        count (int or None): Number of records to return, or None for all.

    Returns:
        list: List of rows fetched from the database.
    """
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if count is not None and isinstance(count, int) and 1 <= count <= MAX_RECORDS:
        query = f"{base_query} LIMIT ?"
        cursor.execute(query, (count,))
    else:
        cursor.execute(base_query)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_count_param():
    """Helper to parse ?count= from query string."""
    count = request.args.get("count")
    try:
        return int(count) if count is not None else None
    except ValueError:
        return None

@app.route('/api/sensor_data', methods=['GET'])
def get_sensor_data():
    count = get_count_param()
    query = "SELECT * FROM data ORDER BY timestamp DESC"
    data = fetch_db_data(SENSOR_DB, query, count)
    return jsonify(data)

@app.route('/api/sensor_15min_data', methods=['GET'])
def get_sensor_15min_data():
    count = get_count_param()
    query = "SELECT * FROM data ORDER BY timestamp DESC"
    data = fetch_db_data(HISTORY_15MIN_DB, query, count)
    return jsonify(data)

@app.route('/api/sensor_hourly_data', methods=['GET'])
def get_sensor_hourly_data():
    count = get_count_param()
    query = "SELECT * FROM data ORDER BY timestamp DESC"
    data = fetch_db_data(HISTORY_HOURLY_DB, query, count)
    return jsonify(data)

@app.route('/api/mgmt_data', methods=['GET'])
def get_mgmt_data():
    count = get_count_param()
    query = "SELECT * FROM data ORDER BY timestamp DESC"
    data = fetch_db_data(MGMT_DB, query, count)
    return jsonify(data)

@app.route('/api/gpio_data', methods=['GET'])
def get_gpio_data():
    count = get_count_param()
    query = "SELECT * FROM data ORDER BY timestamp DESC"
    data = fetch_db_data(GPIO_DB, query, count)
    return jsonify(data)

@app.route('/api/mgmt_changes', methods=['GET'])
def get_mgmt_changes():
    count = get_count_param()
    query = "SELECT * FROM data ORDER BY timestamp DESC"
    data = fetch_db_data(MGMT_CHANGES_DB, query, count)
    return jsonify(data)

@app.route('/api/gpio_changes', methods=['GET'])
def get_gpio_changes():
    count = get_count_param()
    query = "SELECT * FROM data ORDER BY timestamp DESC"
    data = fetch_db_data(GPIO_CHANGES_DB, query, count)
    return jsonify(data)

@app.route('/api/monitor', methods=['GET'])
def get_monitor_file():
    """
    API endpoint to export the contents of monitor.txt as JSON.

    Returns:
        JSON: A dictionary containing the file's contents or an error message if the file is missing.
    """       
    if os.path.exists(MONITOR_FILE):
        try:
            # Read the contents of the file                                          
            with open(MONITOR_FILE, "r") as file:
                file_contents = file.read().strip()
            # Return the file contents as JSON                                              
            return jsonify({"status": "success", "contents": file_contents})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "error", "message": f"File '{MONITOR_FILE}' not found."})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002, use_reloader=False)                                                                      
#    app.run(host='0.0.0.0', port=5002, use_reloader=False)
