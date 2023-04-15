import serial
import time

# Configure the serial connection
ser = serial.Serial(
    port="/dev/serial0",  # Replace with "/dev/ttyS0" for older Raspberry Pi models
    baudrate=9600,
    timeout=1
)

# Function to send a command to the SIM800L module
def send_command(cmd, wait_time=1):
    ser.write((cmd + '\r\n').encode())
    time.sleep(wait_time)
    response = ser.read_all().decode('utf-8', errors='ignore')
    print(response)

def send_sms(phone_number, message):
    send_command("AT+CMGF=1")  # Set the SMS mode to text
    send_command(f'AT+CMGS={phone_number}', wait_time=2)  # Set the recipient's phone number
    ser.write((message + '\x1A').encode())  # Send the message followed by the Ctrl+Z character (0x1A)
    time.sleep(3)  # Wait for the message to be sent
    response = ser.read_all().decode('utf-8', errors='ignore')
    print(response)

recipient_number = "09309118777"
message_text = "Hello, this is a test message from my Raspberry Pi and SIM800L module!"

send_command("AT+CREG?")
send_command("AT+CSQ")
send_sms(recipient_number, message_text)

# Close the serial connection
ser.close()
