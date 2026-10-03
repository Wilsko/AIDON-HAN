echo "Verifying installation ..."

# 1. Check Python imports
echo -n "Checking Python module imports... "
python3 - << 'EOF'
import sys

modules = [
    "flask",
    "flask_cors",
    "smbus2",
    "pytz",
    "ASUS.GPIO",
    "adafruit_blinka",
    "adafruit_bus_device"
]

failed = []
for m in modules:
    try:
        __import__(m)
    except Exception as e:
        failed.append((m, str(e)))

if failed:
    print("FAILED")
    for m, err in failed:
        print(f"  - {m}: {err}")
    sys.exit(1)
else:
    print("OK")
EOF

echo -n "Checking Blinka import... "
python3 - << 'EOF'
try:
    import adafruit_blinka
    print("OK")
except Exception as e:
    print("FAILED:", e)
EOF



# 3. Check I2C bus availability
echo -n "Checking I2C bus... "
if [ -e /dev/i2c-1 ]; then
    echo "OK (/dev/i2c-1 found)"
else
    echo "FAILED (no /dev/i2c-1)"
fi

# 4. Check serial port availability
echo -n "Checking serial ports... "
if ls /dev/ttyS* >/dev/null 2>&1; then
    echo "OK"
else
    echo "FAILED (no /dev/ttyS*)"
fi

# 5. Check SQLite
echo -n "Checking SQLite... "
sqlite3 --version >/dev/null 2>&1 && echo "OK" || echo "FAILED"

# 6. Check Nginx config
echo -n "Checking Nginx configuration... "
sudo nginx -t >/dev/null 2>&1 && echo "OK" || echo "FAILED"

# 7. Check API health
echo -n "Checking API endpoint... "
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/api/mgmt_data?count=1 | grep -q "200"; then
    echo "OK"
else
    echo "FAILED"
fi

echo -n "Checking local user access to /opt/hservice... "
LOCAL_USER="$(logname)"

if sudo -u "$LOCAL_USER" test -r /opt/hservice; then
    echo "OK"
else
    echo "FAILED (user $LOCAL_USER cannot read /opt/hservice)"
fi

echo -n "Checking local user access to /opt/hservice/log... "
if sudo -u "$LOCAL_USER" test -r /opt/hservice/log; then
    echo "OK"
else
    echo "FAILED (user $LOCAL_USER cannot read /opt/hservice/log)"
fi


echo "Verify Installation completed."
