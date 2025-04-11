# OH4NLT ASUS Tinkerboard HAN-IO Interface card switch 2 input reader
# Input data to be stored to Sqlite3 db
# 11.4.2025 VP with Copilot

import ASUS.GPIO as GPIO
import time

# Pin number (based on GPIO numbering)
# Check it out, differ from RPi

PIN_NUMBER = 33

# Set up GPIO mode

GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
GPIO.setup(PIN_NUMBER, GPIO.IN)  # Set pin 33 as an input

try:
    while True:
        # Read the state of the pin
        pin_state = GPIO.input(PIN_NUMBER)
        
        # Print the result
        print(f"GPIO Pin {PIN_NUMBER} State: {'HIGH' if pin_state else 'LOW'}")
        
        # Delay for better readability
        time.sleep(3)
except KeyboardInterrupt:
    print("Exiting program.")
finally:
    GPIO.cleanup()  # Clean up GPIO settings
