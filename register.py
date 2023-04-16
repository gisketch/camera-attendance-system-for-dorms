import cv2
import os
import json
import face_recognition

def capture_tenant_image(first_name, last_name):
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('Camera Feed')

    while True:
        ret, frame = cap.read()
        cv2.imshow('Camera Feed', frame)

        key = cv2.waitKey(1)
        if key & 0xFF == ord('c'):  # Press 'c' to capture the image
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)

            if len(face_locations) == 1:  # Check if there's exactly one face in the frame
                image_filename = f"{first_name}_{last_name}.jpg"
                image_path = os.path.join("tenants", image_filename)
                cv2.imwrite(image_path, frame)
                break
            elif len(face_locations) == 0:
                print("No face detected. Please try again.")
            else:
                print("Multiple faces detected. Please make sure only the tenant's face is in the frame and try again.")
        elif key & 0xFF == ord('q'):  # Press 'q' to quit without capturing the image
            break

    cap.release()
    cv2.destroyAllWindows()

def save_tenant_data(first_name, last_name, email, parents_phone):
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "parents_phone": parents_phone
    }

    json_filename = "tenants_data.json"
    if os.path.exists(json_filename):
        with open(json_filename, 'r') as file:
            file_contents = file.read()
            if file_contents:
                tenants_data = json.loads(file_contents)
            else:
                tenants_data = {}
    else:
        tenants_data = {}

    key = f"{first_name}_{last_name}"
    tenants_data[key] = data

    with open(json_filename, 'w') as file:
        json.dump(tenants_data, file, indent=4)

def main():
    first_name = input("Enter tenant's first name: ")
    last_name = input("Enter tenant's last name: ")
    email = input("Enter tenant's email: ")
    parents_phone = input("Enter tenant's parents' phone number: ")

    save_tenant_data(first_name, last_name, email, parents_phone)
    capture_tenant_image(first_name, last_name)
    input("Tenant data saved successfully. Press any key to continue...")

if __name__ == "__main__":
    main()

       
