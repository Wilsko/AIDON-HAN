# MGMT DATA READER
# 17.4.2025 VP,Copilot
#
# Reads asus serial port ttyS4 and stores the input
# to mgmt_data database
# Reports the changes in switch state into mgmt_changes database
# 0.4 25.4.2025 Changes in screen output to include database name for clarify
# 0.5 12.2.2026 Added CPU temp and TCN75 PCB Temp read. Values added to the end of data field's list.
#               Correction to logic: All the records older than time limit will be deleted, not just the last one.
#               Added timeout to management connection
# 0.8 2.3.2026  Added report mail when switch changes
# 0.9 4.3.2026  Added alert mail on CPU and PCB overheating
# 1.0 5.3.2026  sw1_state
#                0:   HAN System: Kotelon ovi kiinni
#                1:   HAN System Alert: Kotelon ovi auki
#                HAN System: Switch 1 (Serial port) change detected 
# 1.1 10.4.2026 Version info
# 1.2 19.4.2026 Safe alertmail.config read
# 1.3 12.5.2026  Corrected sw1 alert texts
#                0:   HAN System: Ukkossuoja OK
#                1:   HAN System Alert: Ukkossuoja lauennut
#                Alert mail texts changed
# 1.4 12.8.2026 Delayed start after smbus loaf
# 1.5 29.8.2026 Improved error handling in main()
#
# version info 0.1.5

VERSION="0.1.5"

# Start delay: Wait for 10 seconds
import time
import sys
if "--version" in sys.argv:
    print(VERSION)
    sys.exit(0)

import serial
import sqlite3
import os
import smbus2
from datetime import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
import platform

NEWLINE='\n'

I2C_BUS = 6
TCN75_ADDRESS = 0x48
TEMP_REGISTER = 0x00
READ_INTERVAL = 10

bus = smbus2.SMBus(I2C_BUS)

START_DELAY=5
print(f"{__file__} version {VERSION} -- Delayed start ...")
time.sleep(START_DELAY)
print(f"{__file__} version {VERSION} starting")

DB_MAIN = "mgmt_data.db"
DB_CHANGES = "mgmt_changes.db"
MAX_RECORDS = 100

PCB_TEMP_WARNING_ACTIVE = False # global alert state flag
CPU_TEMP_WARNING_ACTIVE = False # global alert state flag

# Path to CPU temperature file (common for Tinker Board)
temp_path = "/sys/class/thermal/thermal_zone0/temp"

_last_pcb_error_time = 0   # prevent log spam
ERROR_INTERVAL = 60        # log at most once per minute

VALID_PORTS = {"465", "587"}   # SSL/TLS or STARTTLS

def safe_str_to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def load_mail_config(filename="alertmail.config"):
    """
    Safely load and validate alert mail configuration.
    Returns a dict with typed values or raises ValueError with a clear message.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Config file not found: {filename}")

    raw = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"Invalid config line (missing '='): {line}")
            key, value = line.split("=", 1)
            raw[key.strip()] = value.strip()

    # Required string fields
    required_keys = ["server", "port", "from_addr", "password", "to_addr",
                     "pcb_hot", "hysteresis", "cpu_hot", "enabled"]

    for key in required_keys:
        if key not in raw:
            raise ValueError(f"Missing required config key: {key}")

    # Validate port
    port = raw["port"]
    if port not in VALID_PORTS:
        raise ValueError(f"Invalid port '{port}'. Must be one of: {', '.join(VALID_PORTS)}")

    # Convert numeric fields
    pcb_hot = safe_str_to_int(raw["pcb_hot"])
    hysteresis = safe_str_to_int(raw["hysteresis"])
    cpu_hot = safe_str_to_int(raw["cpu_hot"])
    enabled = safe_str_to_int(raw["enabled"])
    
    if pcb_hot is None or hysteresis is None or cpu_hot is None:
        raise ValueError("Numeric fields pcb_hot, hysteresis, cpu_hot must be valid integers.")

    # Return typed config
    return {
        "enabled": enabled,
        "server": raw["server"],
        "port": port,
        "from_addr": raw["from_addr"],
        "password": raw["password"],
        "to_addr": raw["to_addr"],
        "pcb_hot": pcb_hot,
        "hysteresis": hysteresis,
        "cpu_hot": cpu_hot,
    }


def send_alert(subject, body):
    
    try:
        cfg = load_mail_config("/opt/hservice/alertmail.config")
    except Exception as e:
        log.error(f"Mail config error: {e}")
        return
    print(cfg)
    
    servername=cfg["server"]
    port=cfg["port"]
    from_addr=cfg["from_addr"]
    password=cfg["password"]
    to_addr=cfg["to_addr"]
    stamp=get_local_time()
    date_time = stamp.strftime("%d.%m.%Y  %H:%M:%S")
    host=platform.node()
    message = host+NEWLINE+date_time+NEWLINE+body 
    #    message=body
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    print(f"From: {from_addr}, To: {to_addr}")
    print(f"mail enabled = {cfg['enabled']}")
    if cfg["enabled"] == 1:
        with smtplib.SMTP_SSL(servername, port, timeout=10) as server:
            server.set_debuglevel(0)
            server.login(from_addr, password)
            server.send_message(msg)

# String to integer conversion in Python

def safe_str_to_int(s: str, base: int = 10) -> int:
    """
    Convert a string to an integer safely.
    
    :param s: The string to convert.
    :param base: The numeric base (default is 10).
    :return: The integer value.
    :raises ValueError: If the string is not a valid integer.
    :
    :returns zero on errors
    """
    if not isinstance(s, str):
        raise TypeError("Input must be a string.")
        return 0
    
    s = s.strip()  # Remove leading/trailing spaces
    
    if s == "":
        raise ValueError("Empty string cannot be converted to integer.")
        return 0
    try:
        return int(s, base)
    except ValueError:
        raise ValueError(f"'{s}' is not a valid integer in base {base}.")
        return 0


def get_local_time():
    """
    Returns the current local time adjusted for the system's local timezone.
    """
    # Replace 'Europe/Helsinki' with your local timezone
    local_timezone = pytz.timezone("Europe/Helsinki")

    # Get current UTC time and convert to local time
    local_time = datetime.now(pytz.utc).astimezone(local_timezone)
    return local_time

def read_pcb_temp():
    """Reads temperature from the TCN75 sensor safely.
       Returns float °C or None on failure.
    """
    hysteresis = 2  # degrees C
    pcb_hot = 30
    global _last_pcb_error_time
    global PCB_TEMP_WARNING_ACTIVE
    cfg = load_mail_config()
    
#    pcb_hot=safe_str_to_int(cfg["pcb_hot"])
#    hysteresis=safe_str_to_int(cfg["hysteresis"])
    pcb_hot=cfg["pcb_hot"]
    hysteresis=cfg["hysteresis"]
    print(f"PCB HOT LIMIT {pcb_hot} C, hysteresis {hysteresis} C")
    
    try:
        raw_data = bus.read_word_data(TCN75_ADDRESS, TEMP_REGISTER)

        # Swap bytes (TCN75 stores MSB first)
        raw_data = ((raw_data << 8) & 0xFF00) | (raw_data >> 8)

        # Extract temperature (12-bit resolution)
        temp_celsius = raw_data >> 4

        # Handle negative temperatures
        if temp_celsius & (1 << 11):
            temp_celsius -= 1 << 12
        
        temp_celsius = temp_celsius * 0.0625
        
        print(f"T:{temp_celsius} WA:{PCB_TEMP_WARNING_ACTIVE}")    
        
     # --- Hysteresis logic ---
        if not PCB_TEMP_WARNING_ACTIVE:
            # Warning is currently OFF → trigger only if above high threshold
            if temp_celsius > pcb_hot:
                print(f"T:{temp_celsius} WA:{PCB_TEMP_WARNING_ACTIVE}, Send Alert")
                send_alert(
                    subject="HAN System Warning: PCB Temp high",
                    body=f"PCB Temp {temp_celsius}, limit {pcb_hot}"
                )
                PCB_TEMP_WARNING_ACTIVE = True

        else:
            # Warning is currently ON → clear only if below low threshold
            if temp_celsius < (pcb_hot - hysteresis):
                print(f"T:{temp_celsius} WA:{PCB_TEMP_WARNING_ACTIVE}, Send Normal Msg")
                send_alert(
                    subject="HAN System: PCB Temp normal",
                    body=f"PCB Temp {temp_celsius} C, limit {pcb_hot} C"
                )
                PCB_TEMP_WARNING_ACTIVE = False
                
        return temp_celsius

    except Exception as e:
        now = time.time()
        print(f"[WARN] PCB temperature read failed: {e}")

        # Log only once per minute to avoid flooding
        if now - _last_pcb_error_time > ERROR_INTERVAL:
            print(f"[WARN] PCB temperature read failed: {e}")
            _last_pcb_error_time = now

        return None

def get_cpu_temp():
    
    global CPU_TEMP_WARNING_ACTIVE
    hysteresis = 2  # degrees C
    cpu_hot=45
    cfg = load_mail_config()

#    cpu_hot=safe_str_to_int(cfg["cpu_hot"])
#    hysteresis=safe_str_to_int(cfg["hysteresis"])
    cpu_hot=cfg["cpu_hot"]
    hysteresis=cfg["hysteresis"]
    print(f"CPU HOT LIMIT {cpu_hot} C, hysteresis {hysteresis} C")

    try:
        with open(temp_path, "r") as f:
            temp_milli = int(f.read().strip())
            

        temp_celsius = round(temp_milli / 1000.0,0)  # Convert to °C
        if temp_celsius > cpu_hot:
            anomaly_detected = True
          

        print(f"T:{temp_celsius} WA:{CPU_TEMP_WARNING_ACTIVE}")
      
        
        # --- Hysteresis logic ---
        if not CPU_TEMP_WARNING_ACTIVE:
            # Warning is currently OFF → trigger only if above high threshold
            if temp_celsius > cpu_hot:
                print(f"T:{temp_celsius} WA:{CPU_TEMP_WARNING_ACTIVE}, Send Alert")
                send_alert(
                    subject="HAN System Warning: CPU Temp high",
                    body=f"CPU Temp {temp_celsius} C, limit {cpu_hot} C"
                )
                CPU_TEMP_WARNING_ACTIVE = True

        else:
            # Warning is currently ON → clear only if below low threshold
            if temp_celsius < (cpu_hot - hysteresis):
                print(f"T:{temp_celsius} WA:{CPU_TEMP_WARNING_ACTIVE}, Send Normal Msg")
                send_alert(
                    subject="HAN System: CPU Temp normal",
                    body=f"CPU Temp {temp_celsius} C, limit {cpu_hot} C"
                )
                CPU_TEMP_WARNING_ACTIVE = False

        # Return temperature as string with 0.1°C resolution
        temp_celsius = round(temp_milli / 1000.0, 1)
        return str(temp_celsius)
    
        return str(temp_celsius) 
        
    except FileNotFoundError:
        return None
  

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def initialize_database(db_file):
    """Creates the 'data' table if it doesn't exist."""
    conn = create_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            timestamp INTEGER PRIMARY KEY,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()

def store_data(db_file, timestamp, data):
    """Stores timestamp and serial data in the specified database."""
    conn = create_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO data (timestamp, data) VALUES (?, ?)", (timestamp, data))
    conn.commit()
    conn.close()

def remove_old_records(db_file, max_records=None):
    """
    Removes records from the specified database.
    - If max_records is specified, ensures the table contains at most max_records entries.
    """
    conn = create_connection(db_file)
    cursor = conn.cursor()

    if max_records:
        cursor.execute("SELECT COUNT(*) FROM data")
        record_count = cursor.fetchone()[0]
        print(f"Record count {record_count}")
        if record_count > max_records:
            # print("Max records reached, deleting old records")
            print(f"Deleting old records in {db_file}  ({record_count})")
            cursor.execute(""" 
                DELETE FROM data 
                WHERE timestamp NOT IN ( 
                    SELECT timestamp FROM data 
                    ORDER BY timestamp DESC LIMIT ? )
            """, (max_records,))
            conn.commit()
    conn.close()

def readManagement(mgmtConnection, previous_s_value=None):
    """Reads serial data from the management connection and processes it safely."""
    
    
    # Clear the input buffer
    mgmtConnection.reset_input_buffer()

    stringData = ""

    # Wait for line beginning with "S" character
    while not stringData.startswith("S"):
        try:
            line = mgmtConnection.readline()
            if not line:
                # Timeout occurred 
                print("[WARN] Serial timeout waiting for S character") 
                return [previous_s_value, "T0", False] # Safe fallback
            
            stringData = line.decode('utf-8', errors='ignore').strip()
        except Exception as e:
            print(f"Garbage in serial port, skipping: {e}")
            return [previous_s_value, "T0", False]

    s_value = stringData  # Value starting with "S"

    # Read next line, should be one starting with "T" character
    try:
        line = mgmtConnection.readline()
    
        if not line: 
            print("[WARN] Serial timeout waiting for T character") 
            return [s_value, "T0", False]
        
        t_value = line.decode('utf-8', errors='ignore').strip() # Value starting with "T"
        
    except Exception as e: 
        print(f"[WARN] Error reading T character: {e}")
        t_value = "T0"   

    # Compare 'S' value with previous and return data
    # Detect change 
    change_detected = (s_value != previous_s_value) 
    return [s_value, t_value, change_detected]
    
import traceback

def main():
    serMgmt = serial.Serial(port="/dev/ttyS4", baudrate=300, timeout=30)
    print("connected to management: " + serMgmt.portstr)

    # Initialize the databases
    initialize_database(DB_MAIN)
    initialize_database(DB_CHANGES)

    previous_s_value = None  # Track last "S" value

    
    while True:
        try:
            # Read data from the serial port
            serial_data, t_value, change_detected = readManagement(serMgmt, previous_s_value)

            # Update "S" value tracker
            previous_s_value = serial_data

            # Prepare the data for storage
            timestamp = int(time.time())
            dt = datetime.fromtimestamp(timestamp)   # local time
            strtime = dt.strftime("%Y-%m-%d %H:%M:%S")
            
#            Previous (before 0.5)  versions:
#            formatted_data = f"{serial_data}, {t_value}"            
#            cpu_temp = get_cpu_temp()
#            formatted_data = f"{serial_data}, {t_value}, CPU:{cpu_temp}"

            cpu_temp = get_cpu_temp()
            pcb_temp = read_pcb_temp()
 #           print(f"main loop: T:{pcb_temp}")
            formatted_data = f"{serial_data}, {t_value}, CPU {cpu_temp}, PCB {pcb_temp} C"

            # Store data in the main database
            store_data(DB_MAIN, timestamp, formatted_data)
            print(f"Data Stored in {DB_MAIN} - Timestamp: {timestamp}, Data: {formatted_data}")

            # Remove old records from the main database
            remove_old_records(DB_MAIN, max_records=MAX_RECORDS)

            # If "S" value has changed, store in the changes database
            # Send report mail if mail enabled
            if change_detected:
                store_data(DB_CHANGES, timestamp, formatted_data)
                print(f"Data Stored in {DB_CHANGES} - Timestamp: {timestamp}, Data: {formatted_data}")
                sw1_state = serial_data[-1] if serial_data else None  # Handles empty string safely
                env_temp = t_value.lstrip("T").strip()
                if sw1_state=="0":
                    send_alert("HAN System: Ukkossuoja Ok",f"Serial Data S1: {sw1_state}, Env: {env_temp} C, PCB: {pcb_temp} C, CPU: {cpu_temp} C" )
                else:
                    send_alert("HAN System Alert: Ukkossuoja lauennut",f"Serial Data S1: {sw1_state}, Env: {env_temp} C, PCB: {pcb_temp} C, CPU: {cpu_temp} C" )
                print(f"HAN System: Switch 1 (Serial port) change detected ------- Switch 1: {sw1_state}, Env: {env_temp} C, PCB: {pcb_temp} C, CPU: {cpu_temp} C" )
                # Ensure changes database does not exceed 30 records
                remove_old_records(DB_CHANGES, max_records=MAX_RECORDS)

            # Wait for 10 seconds
            time.sleep(READ_INTERVAL)
        except KeyboardInterrupt:
            print("Program interrupted by user.")
            break
        except Exception as e:
            print(f"readManagement() failed: {e}")
            traceback.print_exc()
            time.sleep(1)  # wait before retry
        else:
            # Optional: if your function is supposed to loop internally,
            # you can sleep here instead.
            time.sleep(0.1)
	
 #       finally:
 #           serMgmt.close()

if __name__ == "__main__":
    main()
