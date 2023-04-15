import pigpio
import time

RX = 23  # GPIO 23 as the receiving pin
TX = 24  # GPIO 24 as the transmitting pin

pi = pigpio.pi()  # Create a pigpio object

# Configure the software serial connection
ser = pi.serial_open(RX, 9600, 8)  # 9600 baud rate, 8 data bits

# Function to send a command to the SIM800L module
def send_command(cmd, wait_time=1):
    pi.serial_write(ser, (cmd + '\r\n').encode())
    time.sleep(wait_time)
    response = pi.serial_read(ser, 1000)  # Read up to 1000 bytes
    print(response.decode('utf-8', errors='ignore'))

# Send some basic commands to the SIM800L module
send_command('AT')  # Check if the module is responding
send_command('AT+CSQ')  # Check the signal quality

# Close the software serial connection
pi.serial_close(ser)
pi.stop()  # Close the pigpio object
