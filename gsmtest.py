import serial
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

RX = 23  # GPIO 23 as the receiving pin
TX = 24  # GPIO 24 as the transmitting pin

# Configure the software serial connection
ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)

# Function to send a command to the SIM800L module
def send_command(cmd, wait_time=1):
    ser.write((cmd + '\r\n').encode())
    time.sleep(wait_time)
    response = ser.read(1000)  # Read up to 1000 bytes
    print(response.decode('utf-8', errors='ignore'))

# Send some basic commands to the SIM800L module
send_command('AT')  # Check if the module is responding
send_command('AT+CSQ')  # Check the signal quality

ser.close()
