# JSON HAN-API 
# sqlite3, json, flask, nginx
# 12.4.2025 VP, Copilot
# Ohjeet Onenotessa
#

from flask import Flask, jsonify
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# SQLite3 database file
DATABASE = "sensor-data.db"

def get_data_from_db():
    """Fetch all rows from the 'data' table in the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data")  # Fetch all rows
    rows = cursor.fetchall()
    conn.close()

    # Convert rows to a list of dictionaries
    data = [{"timestamp": row[0], "sensor_data": row[1]} for row in rows]
    return data

@app.route("/api/data", methods=["GET"])
def api_data():
    """API endpoint to export data as JSON."""
    try:
        data = get_data_from_db()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
