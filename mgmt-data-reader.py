import serial

def readManagement(mgmtConnection):
    # clear the input buffer
    mgmtConnection.reset_input_buffer()

    myList = []
    stringData = ""
    
    # wait for line beginning with "S" character
    while not stringData.startswith("S"):
        try:
            line = mgmtConnection.readline()
            stringData = line.decode('utf-8').strip()
        except:
            print("Garbage in serial port, skipping")
    myList.append(stringData)
    
    # read next line, should be one starting with "T" character
    line = mgmtConnection.readline()
    stringData = line.decode('utf-8').strip()
    myList.append(stringData)

    return myList

serMgmt = serial.Serial(
	port = "/dev/ttyS4", baudrate = 300
)
print("connected to management: " + serMgmt.portstr)
print(readManagement(serMgmt))
