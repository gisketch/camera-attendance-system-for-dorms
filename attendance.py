import os
import json
import time
import datetime
from gpiozero import Button
from drivers import Lcd, CustomCharacters
from picamera import PiCamera
from face_recognition import load_image_file, face_encodings, compare_faces

# Initialize camera, LCD, and buttons
camera = PiCamera()
lcd = Lcd()
enter_button = Button(17)
exit_button = Button(27)

# Initialize GSM module (SIM800L)
# (Assuming you've already set up the GSM module with the Raspberry Pi)

def take_photo():
    camera.capture('photo.jpg')

def recognize_face(known_encodings, known_names):
    unknown_image = load_image_file('photo.jpg')
    unknown_encoding = face_encodings(unknown_image)[0]

    results = compare_faces(known_encodings, unknown_encoding, tolerance=0.5)
    name = "Unknown"
    for index, is_match in enumerate(results):
        if is_match:
            name = known_names[index]
            break

    return name

def update_database(name, action):
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    record = {'name': name, 'action': action, 'timestamp': timestamp}

    if not os.path.exists('attendance.json'):
        with open('attendance.json', 'w') as f:
            json.dump([], f)

    with open('attendance.json', 'r') as f:
        data = json.load(f)

    data.append(record)

    with open('attendance.json', 'w') as f:
        json.dump(data, f)

def main():
    # Load known faces and their encodings
    known_encodings = []  # Load your known face encodings here
    known_names = []  # Load your known face names here

    while True:
        if enter_button.is_pressed:
            time.sleep(0.5)
            take_photo()
            name = recognize_face(known_encodings, known_names)
            update_database(name, "Enter")
            lcd.lcd_display_string(name, 1)
            lcd.lcd_display_string("Recognized", 2)
            time.sleep(2)
            lcd.lcd_clear()

        if exit_button.is_pressed:
            time.sleep(0.5)
            take_photo()
            name = recognize_face(known_encodings, known_names)
            update_database(name, "Exit")
            lcd.lcd_display_string(name, 1)
            lcd.lcd_display_string("Recognized", 2)
            time.sleep(2)
            lcd.lcd_clear()

if __name__ == '__main__':
    main()
