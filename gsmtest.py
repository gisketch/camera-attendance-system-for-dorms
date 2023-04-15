import serial
import time

# Set up the serial communication with SIM800L module
ser = serial.Serial('/dev/serial0', 9600, timeout=1)

# Turn on the SIM800L module
ser.write(b'AT+CFUN=1\r\n')
time.sleep(1)

# Set the module to text mode
ser.write(b'AT+CMGF=1\r\n')
time.sleep(1)

# Set the phone number to which you want to send the SMS
phone_number = "+639309118777"

# Set the SMS text message
sms_message = "Hello from Raspberry Pi!"

# Send the SMS
ser.write(b'AT+CMGS="' + phone_number.encode() + b'"\r\n')
time.sleep(1)
ser.write(sms_message.encode() + b"\r\n")
time.sleep(1)
ser.write(bytes([26]))

# Wait for the module to send the SMS
time.sleep(10)

# Read the response from the module
response = ser.read(ser.inWaiting())
print(response.decode())

# Close the serial communication
ser.close()
