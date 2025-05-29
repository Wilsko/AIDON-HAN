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
# 3.5.2025 changed MONITOR_FILE = "watchdog.txt"
from flask import Flask, jsonify
from flask_cors import CORS
# CORS was needed fro security comptibility when nginx is not in use
import sqlite3

app = Flask(__name__)
CORS(app)  # Allow all origins for simplicity
# Database file paths
SENSOR_DB = "sensor_data.db"
MGMT_DB = "mgmt_data.db"
GPIO_DB = "gpio_data.db"
MGMT_CHANGES_DB = "mgmt_changes.db"
GPIO_CHANGES_DB = "gpio_changes.db"

MONITOR_FILE = "watchdog.txt"

def fetch_all_data(db_file, query):
    """
    Fetch all rows from the specified database using the provided query.

    Args:
        db_file (str): Path to the SQLite database file.
        query (str): SQL query to execute.

    Returns:
        list: List of rows fetched from the database.
    """
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row  # Enable row access by column name
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.route('/api/sensor_data', methods=['GET'])
def get_sensor_data():
    """
    API endpoint to retrieve data from sensor_data.db.

    Returns:
        JSON: All rows from the data table in sensor_data.db.
    """
    query = "SELECT * FROM data order by timestamp desc"
    data = fetch_all_data(SENSOR_DB, query)
    return jsonify(data)

@app.route('/api/mgmt_data', methods=['GET'])
def get_mgmt_data():
    """
    API endpoint to retrieve data from mgmt_data.db.

    Returns:
        JSON: All rows from the data table in mgmt_data.db.
    """
    query = "SELECT * FROM data order by timestamp desc"
    data = fetch_all_data(MGMT_DB, query)
    return jsonify(data)

@app.route('/api/gpio_data', methods=['GET'])
def get_gpio_data():
    """
    API endpoint to retrieve data from gpio_data.db.

    Returns:
        JSON: All rows from the data table in gpio_data.db.
    """
    query = "SELECT * FROM data order by timestamp desc"
    data = fetch_all_data(GPIO_DB, query)
    return jsonify(data)

@app.route('/api/mgmt_changes', methods=['GET'])
def get_mgmt_changes():
    """
    API endpoint to retrieve data from mgmt_changes.db.

    Returns:
        JSON: All rows from the data table in mgmt_changes.db
    """
    query = "SELECT * FROM data order by timestamp desc"
    data = fetch_all_data(MGMT_CHANGES_DB, query)
    return jsonify(data)
	
@app.route('/api/gpio_changes', methods=['GET'])
def get_gpio_changes():
    """
    API endpoint to retrieve data from gpio_changes.db.

    Returns:
        JSON: All rows from the data table in gpio_changes.db
    """
    query = "SELECT * FROM data order by timestamp desc"
    data = fetch_all_data(GPIO_CHANGES_DB, query)
    return jsonify(data)
	
import os

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
