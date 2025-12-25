import cv2
import pickle
import numpy as np

POSITIONS_FILE = "data/CarParkPos"
CAMERA_INDEX = 0 # Check your camera index!

try:
    with open(POSITIONS_FILE, 'rb') as f:
        posList = pickle.load(f)
except:
    posList = []

# Temporary list for drawing the current polygon
current_points = []

def mouse_events(event, x, y, flags, params):
    global current_points, posList

    if event == cv2.EVENT_LBUTTONDOWN:
        # Add a point
        if len(current_points) < 4:
            current_points.append((x, y))
        
        # If 4 points are reached, save the polygon
        if len(current_points) == 4:
            posList.append(np.array(current_points, dtype=np.int32))
            current_points = [] # Reset for next spot
            
            # Save immediately
            with open(POSITIONS_FILE, 'wb') as f:
                pickle.dump(posList, f)

    elif event == cv2.EVENT_RBUTTONDOWN:
        # Right click to remove the polygon you clicked inside
        for i, poly in enumerate(posList):
            # Check if click is inside this polygon
            if cv2.pointPolygonTest(poly, (x, y), False) >= 0:
                posList.pop(i)
                with open(POSITIONS_FILE, 'wb') as f:
                    pickle.dump(posList, f)
                break

def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cv2.namedWindow("Parking Setup")
    cv2.setMouseCallback("Parking Setup", mouse_events)

    print("--- POLYGON SETUP MODE ---")
    print("1. Click 4 POINTS to define a spot.")
    print("2. RIGHT CLICK on a spot to delete it.")
    print("3. Press 'Q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Draw saved spots
        for poly in posList:
            cv2.polylines(frame, [poly], True, (0, 255, 0), 2)

        # Draw current points being clicked
        for pt in current_points:
            cv2.circle(frame, pt, 5, (0, 0, 255), -1)
        
        # Draw lines connecting current points
        if len(current_points) > 1:
            cv2.polylines(frame, [np.array(current_points)], False, (0, 0, 255), 2)

        cv2.imshow("Parking Setup", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()