import RPi.GPIO as GPIO
import time

# Use the BCM numbering scheme for the GPIO pins
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin numbers for the buttons
button1_pin = 17
button2_pin = 27
# Define the GPIO pin number for the door sensor
door_sensor_pin = 22


# Set up the GPIO pins as inputs with internal pull-up resistors enabled
GPIO.setup(button1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(door_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button1_callback(channel):
    print("Button 1 pressed")

def button2_callback(channel):
    print("Button 2 pressed")

def door_sensor_callback(channel):
    if GPIO.input(door_sensor_pin):
        print("Door opened")
    else:
        print("Door closed")


# Set up the interrupt-driven callback for the door sensor
GPIO.add_event_detect(door_sensor_pin, GPIO.BOTH, callback=door_sensor_callback, bouncetime=300)
# Set up the interrupt-driven callbacks for the buttons
GPIO.add_event_detect(button1_pin, GPIO.FALLING, callback=button1_callback, bouncetime=300)
GPIO.add_event_detect(button2_pin, GPIO.FALLING, callback=button2_callback, bouncetime=300)

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Cleaning up...")
    GPIO.cleanup()
