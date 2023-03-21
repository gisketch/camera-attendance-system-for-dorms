import os
import cv2
import face_recognition
import RPi.GPIO as GPIO
from time import sleep
import I2C_LCD_driver
from datetime import datetime
from gsmmodem.modem import GsmModem

# Button and door sensor pins
BUTTON_ENTER_PIN = 20
BUTTON_EXIT_PIN = 21
DOOR_SENSOR_PIN = 18

# Initialize GSM modem
GSM_PORT = "/dev/ttyUSB0"
GSM_BAUDRATE = 115200

# Initialize I2C LCD
lcd = I2C_LCD_driver.lcd()

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_ENTER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_EXIT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOOR_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Load face database
face_db_path = "face_database"
face_encodings, face_names = [], []
for filename in os.listdir(face_db_path):
    if filename.endswith(".jpg"):
        image = face_recognition.load_image_file(os.path.join(face_db_path, filename))
        face_encoding = face_recognition.face_encodings(image)[0]
        face_name = os.path.splitext(filename)[0]
        face_encodings.append(face_encoding)
        face_names.append(face_name)

def capture_image():
    # Capture image from camera
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    return frame

def recognize_face(image):
    # Detect face in image and try to recognize it
    face_locations = face_recognition.face_locations(image)
    if not face_locations:
        return None
    face_encodings = face_recognition.face_encodings(image, face_locations)
    matches = face_recognition.compare_faces(face_encodings, face_encodings[0])
    if True in matches:
        first_match_index = matches.index(True)
        return face_names[first_match_index]
    return None

def send_sms(phone_number, message):
    modem = GsmModem(GSM_PORT, GSM_BAUDRATE)
    modem.connect()
    modem.send_sms(phone_number, message)
    modem.close()

def door_sensor_triggered():
    return GPIO.input(DOOR_SENSOR_PIN) == GPIO.LOW

def is_curfew_violation(curfew_time):
    return datetime.now().time() > curfew_time

try:
    while True:
        # Prompt user for input
        user_input = input("Enter 'i' for entering, 'o' for exiting or 'q' to quit: ")

        if user_input == 'q':
            break

        enter_action = user_input == 'i'
        exit_action = user_input == 'o'

        if enter_action or exit_action:
            lcd.lcd_display_string("Processing...", 1)

            # Capture image and recognize face
            image = capture_image()
            recognized_name = recognize_face(image)

            if recognized_name:
                if enter_action:
                    action = "Entered"
                else:
                    action = "Exited"

                lcd.lcd_clear()
                lcd.lcd_display_string(f"{recognized_name}", 1)
                lcd.lcd_display_string(f"{action}", 2)

                # Simulate door sensor being triggered
                input("Press 'd' to simulate door sensor being triggered: ")

                lcd.lcd_clear()
                sleep(1)

            else:
                lcd.lcd_clear()
                lcd.lcd_display_string("Unknown person", 1)
                # Alert landlord by sending SMS or other desired action
                sleep(2)
                lcd.lcd_clear()

        # Check for curfew violations
        curfew_time = datetime.strptime("22:00:00", "%H:%M:%S").time()
        if is_curfew_violation(curfew_time):
            # Send SMS to parent or perform other desired action
            pass

        sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
    lcd.lcd_clear()