import serial

ser = serial.Serial(
	port = "/dev/ttyS4", baudrate = 300
)

print("connected to: " + ser.portstr)
count=1

while True:
    line = ser.readline()
    print(str(count) + str(': ') + str(line))
    count = count+1

ser.close()
