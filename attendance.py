import cv2
import face_recognition
import os
import RPi.GPIO as GPIO
import time
import numpy as np
import datetime
import json

import serial
import time

# Configure the serial connection
ser = serial.Serial(
    port="/dev/serial0",  # Replace with "/dev/ttyS0" for older Raspberry Pi models
    baudrate=9600,
    timeout=1
)

landlord_number = "09300289941"
waiting_time = 10  #Time to wait before alerting intruder
fast_forward_factor = 2  # 5 seconds equals 1 hour (60 minutes)

# Function to send a command to the SIM800L module
def send_command(cmd, wait_time=1):
    ser.write((cmd + '\r\n').encode())
    time.sleep(wait_time)
    response = ser.read_all().decode('utf-8', errors='ignore')
    print(response)


def send_sms(phone_number, message):
    send_command("AT+CFUN=1")  # Set the SMS mode to text
    time.sleep(1)
    send_command("AT+CMGF=1")  # Set the SMS mode to text
    send_command(f'AT+CMGS="{phone_number}"', wait_time=2)  # Set the recipient's phone number
    ser.write((message + '\x1A').encode())  # Send the message followed by the Ctrl+Z character (0x1A)
    time.sleep(3)  # Wait for the message to be sent
    response = ser.read_all().decode('utf-8', errors='ignore')
    print(response)

print("Initializing GPIO connections...")
# Use the BCM numbering scheme for the GPIO pins
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin numbers for the buttons
button1_pin = 17
button2_pin = 27
# Define the GPIO pin number for the door sensor
door_sensor_pin = 22

print("Setting up GPIO pins...")
# Set up the GPIO pins as inputs with internal pull-up resistors enabled
GPIO.setup(button1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(door_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button1_callback(channel):
    global last_door_sensor_triggered, waiting_for_exit, intruder_timer, enter_key_pressed, global_frame, status
    print("Button 1 pressed (Enter)")
    enter_key_pressed = True
    if last_door_sensor_triggered:
        change_status("Enter key pressed")
        recognize_face(global_frame, "Enter")
        last_door_sensor_triggered = False
        intruder_timer = None  # Reset the intruder timer

def button2_callback(channel):
    global last_door_sensor_triggered, waiting_for_exit, intruder_timer, enter_key_pressed, global_frame, status
    print("Button 2 pressed (Exit)")
    if not last_door_sensor_triggered:
        waiting_for_exit = True
        change_status("Exit key pressed")
        recognize_face(global_frame, "Exit")
        last_door_sensor_triggered = False

door_has_opened = False

def door_sensor_callback(channel):
    global door_has_opened
    if GPIO.input(door_sensor_pin):
        door_has_opened = True
        print("Door opened")
    else:
        print("Door closed")
        if(door_has_opened):
            door_has_opened = False
            door_sensor_triggered()

# Set up the interrupt-driven callback for the door sensor
GPIO.add_event_detect(door_sensor_pin, GPIO.BOTH, callback=door_sensor_callback, bouncetime=1000)
# Set up the interrupt-driven callbacks for the buttons
GPIO.add_event_detect(button1_pin, GPIO.FALLING, callback=button1_callback, bouncetime=1000)
GPIO.add_event_detect(button2_pin, GPIO.FALLING, callback=button2_callback, bouncetime=1000)

default_status = "Waiting for Enter/Exit"

status = "Waiting for Enter/Exit"
status_change_time = 0
status_duration = 5  # Duration to keep the changed status (in seconds)

def change_status(new_status):
    global status, status_change_time
    status = new_status
    status_change_time = time.time()

def putText(frame, text, position, font=cv2.FONT_HERSHEY_SIMPLEX, scale=0.7, color=(255, 255, 255), thickness=2):
    cv2.putText(frame, text, position, font, scale, color, thickness, cv2.LINE_AA)

start_time = None

def display_time_and_status(frame):
    global status, start_time, timestamp, timefloat, tenants_data, inside, fast_forward_factor
    # Add a global variable to track if the SMS messages have been sent
    global sms_sent_flag

    # Display the fast-forwarded time at the top right
    current_time = datetime.datetime.now()
    time_elapsed = (datetime.datetime.now() - start_time).total_seconds()
    fast_forwarded_time = current_time + datetime.timedelta(minutes=time_elapsed * fast_forward_factor)
    fast_forwarded_time_str = fast_forwarded_time.strftime('%m/%d/%Y %I:%M %p')
    timefloat = fast_forwarded_time
    timestamp = fast_forwarded_time_str
    size = cv2.getTextSize(fast_forwarded_time_str, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    width = frame.shape[1]
    putText(frame, fast_forwarded_time_str, (width - size[0] - 10, 30))

    # Check if it's 10 PM or 4 AM
    if fast_forwarded_time.hour in [22, 4]:
        if not sms_sent_flag:
            for tenant_name, is_inside in inside.items():
                if not is_inside:
                    tenant_info = tenants_data.get(tenant_name)
                    if tenant_info:
                        phone_number = tenant_info["parents_phone"]
                        print(f"{tenant_name} - {phone_number}")
                        print(f"Sending SMS to {phone_number}...")
                        send_sms(phone_number, f"{tenant_name} is not at the dormitory yet!")
                        print(f"Message: {tenant_name} is at the dormitory yet!")
                else:
                    tenant_info = tenants_data.get(tenant_name)
                    if tenant_info:
                        phone_number = tenant_info["parents_phone"]
                        print(f"{tenant_name} - {phone_number}")
                        print(f"Sending SMS to {phone_number}...")
                        send_sms(phone_number, f"{tenant_name} is inside the dormitory.")
                        print(f"Message: {tenant_name} is inside the dormitory.")
            # Set the flag to True after sending the SMS messages
            sms_sent_flag = True
    else:
        # Reset the flag when the hour changes
        sms_sent_flag = False

    # Display the status at the bottom
    putText(frame, status, (10, frame.shape[0] - 10))

# Load known faces and their encodings
known_faces = []
known_face_encodings = []
known_face_names = []
global_frame = None

inside = {}
log_data = []
timestamp = ""
timefloat = None

def load_tenants_data():
    tenants_data_file = 'tenants_data.json'

    if not os.path.exists(tenants_data_file):
        return {}

    with open(tenants_data_file, 'r') as file:
        data = json.load(file)

    return data

tenants_data = load_tenants_data()
# Assume all tenants are inside at the start
for tenant_name in tenants_data.keys():
    inside[tenant_name] = True

print(inside)

last_door_sensor_time = None
last_door_sensor_triggered = False

waiting_for_exit = False
intruder_timer = None
enter_key_pressed = False

def door_sensor_triggered():
    global last_door_sensor_time, waiting_for_exit, intruder_timer, enter_key_pressed, last_door_sensor_triggered
    print("Door triggered...")

    last_door_sensor_time = time.time()
    last_door_sensor_triggered = True
    if waiting_for_exit:
        change_status("Door opened (a tenant left)")
        waiting_for_exit = False
    else:
        intruder_timer = time.time()
        change_status("Door opened (waiting for Enter key)")
        enter_key_pressed = False

def load_known_faces():
    
    print("Loading known faces from database...")

    global known_faces, known_face_encodings, known_face_names

    # Set the folder containing the images of known faces
    image_folder = "tenants"

    # Iterate over all image files in the folder
    for file in os.listdir(image_folder):
        # Check if the file is an image (you can add more extensions if needed)
        if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".jpeg"):
            # Load the image and compute the face encoding
            file_path = os.path.join(image_folder, file)
            image = face_recognition.load_image_file(file_path)
            encoding = face_recognition.face_encodings(image)[0]

            # Remove the file extension to get the name
            name = os.path.splitext(file)[0]

            known_faces.append(image)
            known_face_encodings.append(encoding)
            known_face_names.append(name)

def log_event(name, action, parents_phone, email):
    global log_data, status, timestamp
    timestamp_float = float(time.time())
    log_entry = {
        "timestamp": timestamp,
        "timefloat": timestamp_float,
        "name": name,
        "action": action,
        "parents_phone": parents_phone,
        "email": email
    }

    log_file = 'log.json'

    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            file_contents = file.read()
            if file_contents:
                log_data = json.loads(file_contents)
            else:
                log_data = []
    else:
        log_data = []

    log_data.append(log_entry)

    with open(log_file, 'w') as file:
        json.dump(log_data, file, indent=4)

    if action == "Enter":
        inside[name] = True
    elif action == "Exit":
        inside[name] = False
      
    print(f"{name} - {action} - {timestamp}")
    change_status(f"Logged - {name} - {action}")

# def recognize_face(frame, action):
#     global last_door_sensor_time
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     face_locations = face_recognition.face_locations(rgb_frame)

#     print("Recognizing...")

#     if len(face_locations) == 0:
#         print("No face detected. Canceling the process.")
#         return
    
#     elif len(face_locations) > 1:
#         print("Multiple faces detected. Try again.")
#         return

#     face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

#     for face_encoding, face_location in zip(face_encodings, face_locations):
#         matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
#         name = "Unknown"

#         if True in matches:
#             first_match_index = matches.index(True)
#             name = known_face_names[first_match_index]

#         print(name)

#         if name in inside:
#             if inside[name] and action == "Enter":
#                 print(f"{name} is already inside. Ignoring entry event.")
#                 return
#             elif not inside[name] and action == "Exit":
#                 print(f"{name} is already outside. Ignoring exit event.")
#                 return

#         tenant_data = tenants_data.get(name)
#         if tenant_data:
#             parents_phone = tenant_data["parents_phone"]
#             email = tenant_data["email"]
#             log_event(name, action, parents_phone, email)
#         else:
#             log_event(name, action, "...", "...")

def recognize_face(frame, action):
    global last_door_sensor_time
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)

    print("Recognizing...")
    change_status("Recognizing face... wait a moment")

    if len(face_locations) == 0:
        print("No face detected. Canceling the process.")
        return

    elif len(face_locations) > 1:
        print("Multiple faces detected. Try again.")
        return

    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            # Compute the similarity (1 - distance) as a percentage
            face_distance = face_recognition.face_distance([known_face_encodings[first_match_index]], face_encoding)
            similarity_percentage = (1 - face_distance) * 100

        print(name)

        if name in inside:
            if inside[name] and action == "Enter":
                print(f"{name} is already inside. Ignoring entry event.")
                return
            elif not inside[name] and action == "Exit":
                print(f"{name} is already outside. Ignoring exit event.")
                return

        tenant_data = tenants_data.get(name)
        if tenant_data:
            parents_phone = tenant_data["parents_phone"]
            email = tenant_data["email"]
            log_event(name, action, parents_phone, email)
        else:
            log_event(name, action, "...", "...")

        # Save the image with bounding box and name
        top, right, bottom, left = face_location
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.putText(frame, f"{name} {float(similarity_percentage):.2f}%", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)


        # Set the folder containing the test images
        test_image_folder = "images_test"
        if not os.path.exists(test_image_folder):
            os.makedirs(test_image_folder)

        # Save the image with the bounding box and name
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        test_image_path = os.path.join(test_image_folder, f"{name}_{timestamp}.jpg")
        cv2.imwrite(test_image_path, frame)

        print(f"Image saved to {test_image_path}")

def get_camera_feed():
    global last_door_sensor_triggered, waiting_for_exit, intruder_timer, enter_key_pressed, global_frame, start_time, status_change_time, status, status_duration, timestamp, waiting_time

    # 10 seconds waiting time

    print("starting camera feed...")
    load_known_faces()
    cap = cv2.VideoCapture(0)

    # Set the window resolution
    window_width, window_height = 1024, 600

    # Set the window to normal and resize it
    cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Camera Feed', window_width, window_height)

    start_time = datetime.datetime.now()
    while True:
        # If the status has changed and the duration has passed, revert it to the default.
        if status != "Waiting for Enter/Exit" and time.time() - status_change_time >= status_duration:
            status = "Waiting for Enter/Exit"

        ret, frame = cap.read()
        global_frame = frame
        display_time_and_status(frame)

        # Resize the camera feed to maintain aspect ratio and center it on the window
        height, width = frame.shape[:2]
        aspect_ratio = float(width) / float(height)
        new_width = window_width
        new_height = int(new_width / aspect_ratio)

        if new_height > window_height:
            new_height = window_height
            new_width = int(new_height * aspect_ratio)

        resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Create a black frame with the window resolution
        black_frame = np.zeros((window_height, window_width, 3), dtype=np.uint8)

        # Place the resized frame in the center of the black frame
        y_offset = (window_height - new_height) // 2
        x_offset = (window_width - new_width) // 2
        black_frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame

        cv2.imshow('Camera Feed', black_frame)

        key = cv2.waitKey(1)
        if key == ord("d"):
            door_sensor_triggered()
        if key == ord("e"):
            print("Enter key pressed")
            enter_key_pressed = True
            if last_door_sensor_triggered:
                recognize_face(frame, "Enter")
                last_door_sensor_triggered = False
                intruder_timer = None  # Reset the intruder timer
        elif key == ord("x"):
            print("Exit key pressed")
            if not last_door_sensor_triggered:
                waiting_for_exit = True
                recognize_face(frame, "Exit")
                last_door_sensor_triggered = False
        elif key & 0xFF == ord('q'):  # Press 'q' to quit the application
            
            print("Cleaning up...")
            GPIO.cleanup()
            # Close the serial connection
            ser.close()
            cv2.destroyAllWindows()
            break

        # Check for possible intruder
        if intruder_timer and time.time() - intruder_timer > waiting_time:
            if not enter_key_pressed:
                send_sms(landlord_number, f"Possible intruder entered the dormitory at {timestamp}")
                log_event("Possible intruder", "Alert", "...", "...")
            intruder_timer = None  # Reset the intruder timer
            last_door_sensor_triggered = False

    cap.release()
    cv2.destroyAllWindows()

sms_sent_flag = False

if __name__ == "__main__":
    # get_image_feed()
    get_camera_feed()
