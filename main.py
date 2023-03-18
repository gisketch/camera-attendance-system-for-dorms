import cv2

# Create a VideoCapture object to capture video from the camera module
cap = cv2.VideoCapture(0)

# Set the resolution of the camera
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Create a window to display the camera feed
cv2.namedWindow("Live Camera View", cv2.WINDOW_NORMAL)

while True:
    # Read a frame from the camera
    ret, frame = cap.read()

    # Display the frame in the window
    cv2.imshow("Live Camera View", frame)

    # Wait for a key press and check if the user wants to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the VideoCapture object and close the window
cap.release()
cv2.destroyAllWindows()