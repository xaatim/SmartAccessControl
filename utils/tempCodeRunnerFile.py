import cv2
import pickle

# --- CONFIG ---
# Width/Height of your parking spots (Adjust to match your screen/camera resolution)
RECT_WIDTH, RECT_HEIGHT = 107, 48 
POSITIONS_FILE = "data/CarParkPos"
CAMERA_INDEX = 0  # The index of your parking camera

try:
    with open(POSITIONS_FILE, 'rb') as f:
        posList = pickle.load(f)
except:
    posList = []

def mouseClick(events, x, y, flags, params):
    if events == cv2.EVENT_LBUTTONDOWN:
        # Add new spot
        posList.append((x, y))
    if events == cv2.EVENT_MBUTTONDOWN:
        # Remove spot
        for i, pos in enumerate(posList):
            x1, y1 = pos
            if x1 < x < x1 + RECT_WIDTH and y1 < y < y1 + RECT_HEIGHT:
                posList.pop(i)

    # Save immediately
    with open(POSITIONS_FILE, 'wb') as f:
        pickle.dump(posList, f)

def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Error: Could not open camera {CAMERA_INDEX}")
        return

    cv2.namedWindow("Parking Setup")
    cv2.setMouseCallback("Parking Setup", mouseClick)

    print("--- SETUP MODE ---")
    print("LEFT CLICK:   Add Spot")
    print("MIDDLE CLICK: Remove Spot")
    print("PRESS 'Q':    Save & Exit")

    while True:
        ret, frame = cap.read()
        if not ret: break

        for pos in posList:
            cv2.rectangle(frame, pos, (pos[0] + RECT_WIDTH, pos[1] + RECT_HEIGHT), (255, 0, 255), 2)

        cv2.imshow("Parking Setup", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()