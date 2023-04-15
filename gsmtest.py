import serial

ser = serial.Serial('/dev/serial0', 9600, timeout=1) # open serial port
ser.flushInput() # flush input buffer

while True:
    message = input("Enter a message to send over serial: ") # get user input
    ser.write((message + '\n').encode()) # write message to serial port
    response = ser.readline().decode().strip() # read response from serial port
    print("Response: " + response) # print response
