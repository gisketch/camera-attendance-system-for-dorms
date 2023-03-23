import cv2
import face_recognition
import os
import time
import drivers
import numpy as np
from datetime import datetime
import json

print("Initializing...")

lcd = drivers.Lcd()
print("LCD initialized")

# Load known faces and their encodings
known_faces = []
known_face_encodings = []
known_face_names = []

def load_tenants_data():
    tenants_data_file = 'tenants_data.json'

    if not os.path.exists(tenants_data_file):
        return {}

    with open(tenants_data_file, 'r') as file:
        data = json.load(file)

    return data

tenants_data = load_tenants_data()

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
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        "timestamp": timestamp,
        "name": name.upper(),
        "action": action,
        "parents_phone": parents_phone,
        "email": email
    }

    log_file = 'log.json'
    log_data = []

    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            log_data = json.load(file)

    log_data.append(log_entry)

    with open(log_file, 'w') as file:
        json.dump(log_data, file, indent=4)

def recognize_face(frame, action):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)

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

        print(name.upper())

        tenant_data = tenants_data.get(name)
        if tenant_data:
            parents_phone = tenant_data["parents_phone"]
            email = tenant_data["email"]
            log_event(name.upper(), action, parents_phone, email)
        else:
            log_event(name.upper(), action, "...", "...")

def process_door_actions(state, key, frame):
    global door_open_timestamp

    user_input = None
    if key == ord('o'):
        user_input = "open_door"
    elif key == ord('e'):
        user_input = "enter"
    elif key == ord('x'):
        user_input = "exit"

    if user_input == "open_door":
        if state == "IDLE":
            door_open_timestamp = time.time()
            state = "DOOR_OPEN"
            print("Door opened.")

    elif user_input == "enter":
        if state == "DOOR_OPEN":
            recognize_face(frame, "entered")
            state = "IDLE"
            print("Entered successfully.")
        else:
            print("Door is not open.")

    elif user_input == "exit":
        if state == "IDLE":
            recognize_face(frame, "exited")
            state = "EXITING"
            door_open_timestamp = time.time()
        else:
            print("Cannot exit while door is open.")

    return state

def get_camera_feed():
    state = "IDLE"
    global door_open_timestamp
    door_open_timeout = 30

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error opening the camera.")
        return None

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        cv2.imshow('Camera Feed', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        state = process_door_actions(state, key, frame)

        # Check if the door_open_timeout has been reached
        if state == "DOOR_OPEN" and time.time() - door_open_timestamp > door_open_timeout:
            print("Alert! Possible intruder inside.")
            log_event("Unknown", "intruder", "Unknown", "Unknown")
            state = "IDLE"

        # Check if the exit timeout has been reached
        if state == "EXITING" and time.time() - door_open_timestamp > door_open_timeout:
            print("Exit timeout reached. Resetting state.")
            state = "IDLE"

    cap.release()
    cv2.destroyAllWindows()

def get_image_feed(directory="testing", display_time=2, fixed_resolution=(640, 480)):
    state = "IDLE"
    global door_open_timestamp
    door_open_timeout = 30

    print("starting camera feed...")
    load_known_faces()

    image_files = [file for file in os.listdir(directory) if file.endswith((".jpg", ".png", ".jpeg"))]

    while True:
        for image_file in image_files:
            file_path = os.path.join(directory, image_file)
            image = cv2.imread(file_path)

            # Resize the image while maintaining aspect ratio
            height, width = image.shape[:2]
            aspect_ratio = float(width) / float(height)
            new_width = fixed_resolution[0]
            new_height = int(new_width / aspect_ratio)

            if new_height > fixed_resolution[1]:
                new_height = fixed_resolution[1]
                new_width = int(new_height * aspect_ratio)

            resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Create a black frame with the fixed resolution
            frame = np.zeros((fixed_resolution[1], fixed_resolution[0], 3), dtype=np.uint8)

            # Place the resized image in the center of the frame
            y_offset = (fixed_resolution[1] - new_height) // 2
            x_offset = (fixed_resolution[0] - new_width) // 2
            frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image

            cv2.imshow('Image Feed', frame)

            start_time = time.time()
            while time.time() - start_time < display_time:
                key = cv2.waitKey(1) & 0xFF

                state = process_door_actions(state, key, frame)

                # Check if the door_open_timeout has been reached
                if state == "DOOR_OPEN" and time.time() - door_open_timestamp > door_open_timeout:
                    print("Alert! Possible intruder inside.")
                    log_event("Unknown", "intruder", "Unknown", "Unknown")
                    state = "IDLE"

                # Check if the exit timeout has been reached
                if state == "EXITING" and time.time() - door_open_timestamp > door_open_timeout:
                    print("Exit timeout reached. Resetting state.")
                    state = "IDLE"
                elif key & 0xFF == ord('q'):  # Press 'q' to quit the application
                    cv2.destroyAllWindows()
                    return

if __name__ == "__main__":
    get_image_feed()
    # get_camera_feed()
