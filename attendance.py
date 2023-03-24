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

inside = {}
log_data = []
waiting_for_exit = False

def load_tenants_data():
    tenants_data_file = 'tenants_data.json'

    if not os.path.exists(tenants_data_file):
        return {}

    with open(tenants_data_file, 'r') as file:
        data = json.load(file)

    return data

tenants_data = load_tenants_data()

last_door_sensor_time = None

def door_sensor_triggered():
    global last_door_sensor_time, waiting_for_exit

    if waiting_for_exit:
        waiting_for_exit = False
        return

    last_door_sensor_time = time.time()
    print("Door sensor triggered.")

def check_intruder():
    global last_door_sensor_time

    if last_door_sensor_time is None:
        return

    time_since_sensor = time.time() - last_door_sensor_time

    if time_since_sensor < 60:  # 1 minute
        return

    intruder_detected = True
    print("Possible intruder! Checking the log...")

    for name, inside_status in inside.items():
        for entry in log_data:
            entry_timefloat = entry.get("timefloat", 0)  # Get the timefloat value, or use 0 as the default
            if (entry_timefloat > last_door_sensor_time - 60 and
                    entry["action"] == "Enter" and entry["name"] == name and inside_status):
                intruder_detected = False
                break

        if not intruder_detected:  # If a tenant was found inside, break the outer loop as well
            break

    if intruder_detected:
        print("Intruder alert!")
        log_event("Unknown", "Intruder", "Unknown", "Unknown")
        last_door_sensor_time = None
    else:
        print("Nevermind, it was a tenant.")
        last_door_sensor_time = None



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
    global log_data
    timestamp_float = float(time.time())
    timestamp_readable = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp_float))
    log_entry = {
        "timestamp": timestamp_readable,
        "timefloat": timestamp_float,
        "name": name,
        "action": action,
        "parents_phone": parents_phone,
        "email": email
    }

    log_file = 'log.json'

    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            log_data = json.load(file)

    log_data.append(log_entry)

    with open(log_file, 'w') as file:
        json.dump(log_data, file, indent=4)

    if action == "Enter":
        inside[name] = True
    elif action == "Exit":
        inside[name] = False
      
    print(f"{name} - {action} - {timestamp_readable}")

def recognize_face(frame, action):
    global last_door_sensor_time
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
        
        if action == "Exit" and name in tenants_data:
            print(f"{name} is exiting.")
            waiting_for_exit = True
            log_event(name, action, tenants_data[name]["parents_phone"], tenants_data[name]["email"])
            inside[name] = False

def get_camera_feed():
    print("starting camera feed...")
    load_known_faces()
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        cv2.imshow('Camera Feed', frame)

        key = cv2.waitKey(1)
        if key == ord("d"):
          door_sensor_triggered()
        if key == ord("e"):
            recognize_face(frame, "Enter")
        elif key == ord("x"):
            recognize_face(frame, "Exit")
        elif key & 0xFF == ord('q'):  # Press 'q' to quit the application
            break
        check_intruder()

    cap.release()
    cv2.destroyAllWindows()

def get_image_feed(directory="testing", display_time=2, fixed_resolution=(640, 480)):
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
                key = cv2.waitKey(1)
                if key == ord("d"):
                  door_sensor_triggered()
                if key == ord("e"):
                    recognize_face(frame, "Enter")
                elif key == ord("x"):
                    recognize_face(frame, "Exit")
                elif key & 0xFF == ord('q'):  # Press 'q' to quit the application
                    cv2.destroyAllWindows()
                    return
                check_intruder()

if __name__ == "__main__":
    get_image_feed()
    # get_camera_feed()
