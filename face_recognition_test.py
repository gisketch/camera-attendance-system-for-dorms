import cv2

def get_camera_feed():
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('Camera Feed', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Camera Feed', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        cv2.imshow('Camera Feed', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    get_camera_feed()