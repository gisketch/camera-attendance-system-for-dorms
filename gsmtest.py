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

# Send some basic commands to the SIM800L module
send_command('AT')  # Check if the module is responding
send_command('AT+CSQ')  # Check the signal quality

# Close the serial connection
ser.close()
