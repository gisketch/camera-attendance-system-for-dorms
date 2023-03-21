import os
import json
from datetime import datetime
from gpiozero import Button
from picamera import PiCamera
from time import sleep
import face_recognition
import cv2
import numpy as np
from drivers import Lcd, CustomCharacters

# Initialize camera and buttons
camera = PiCamera()
enter_button = Button(17)
exit_button = Button(27)

# Define tenants
tenants = {
    "tenant_1": {
        "name": "John Doe",
        "encoding": None,
        "phone": "+1234567890"
    },
    # Add more tenants here
}

# Load face encodings for each tenant
for tenant_id, tenant_data in tenants.items():
    image = face_recognition.load_image_file(f"faces/{tenant_id}.jpg")
    face_encoding = face_recognition.face_encodings(image)[0]
    tenants[tenant_id]["encoding"] = face_encoding

def save_to_database(name, action):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = {"name": name, "action": action, "timestamp": current_time}

    if os.path.exists("attendance.json"):
        with open("attendance.json", "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(record)

    with open("attendance.json", "w") as f:
        json.dump(data, f)

def recognize_face():
    camera.capture("temp.jpg")
    image = face_recognition.load_image_file("temp.jpg")
    face_locations = face_recognition.face_locations(image)

    if len(face_locations) > 0:
        face_encodings = face_recognition.face_encodings(image, face_locations)
        face_enc = face_encodings[0]

        # Compare the face encoding with known tenants
        for tenant_id, tenant_data in tenants.items():
            match = face_recognition.compare_faces([tenant_data["encoding"]], face_enc, tolerance=0.5)
            if match[0]:
                return tenant_data["name"]

    return None

def on_button_press(action):
    lcd.lcd_clear()
    lcd.lcd_display_string("Recognizing...", 1)
    name = recognize_face()

    if name:
        lcd.lcd_clear()
        lcd.lcd_display_string(f"{name}", 1)
        lcd.lcd_display_string(f"{action}", 2)
        save_to_database(name, action)
    else:
        lcd.lcd_clear()
        lcd.lcd_display_string("Unknown face", 1)

# Initialize LCD
lcd = Lcd()

# Main loop
while True:
    if enter_button.is_pressed:
        on_button_press("Entered")
        sleep(1)
    elif exit_button.is_pressed:
        on_button_press("Exited")
        sleep(1)