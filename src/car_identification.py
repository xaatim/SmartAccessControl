import cv2 
import easyocr
import imutils
import numpy as np
from collections import Counter, deque
import re

reader = easyocr.Reader(['en'])


plate_list = deque(maxlen=50)
empty_frame_count = 0 

def get_best_plate(current_list):
    clean_votes = []
    
    malaysia_plate_pattern = r"^[A-Z]{1,10}\d{1,4}[A-Z]?$"

    for raw_line in current_list:
        text = raw_line.split(":")[1] if "Full Plate:" in raw_line else raw_line
        

        clean_text = text.replace(" ", "").strip().upper()  

        if re.match(malaysia_plate_pattern, clean_text):
            clean_votes.append(clean_text)

    if not clean_votes:
        return None
    

    vote_counts = Counter(clean_votes)
    winner, count = vote_counts.most_common(1)[0]
    
    if count < 5:
        return None

    return winner


def IdentifyCar(frame):
    global empty_frame_count
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    filter_img = cv2.bilateralFilter(gray, 11, 17, 17)
    edge = cv2.Canny(filter_img, 30, 200)
    
    ext_count = cv2.findContours(edge.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(ext_count)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    
    location = None
    
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        apprx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)
        if len(apprx) == 4:
            location = apprx
            break
    
    msk = np.zeros(gray.shape, np.uint8)
    
    if location is not None: 

        empty_frame_count = 0 
        
        cv2.drawContours(msk, [location], 0, 255, -1)
        extracted_plate = cv2.bitwise_and(frame, frame, mask=msk)
        
        cv2.imshow('plate_number', extracted_plate)
        
        (x, y) = np.where(msk == 255)
        (x1, y1) = (np.min(x), np.min(y))
        (x2, y2) = (np.max(x), np.max(y))
        final_plate = gray[x1:x2 + 1, y1:y2 + 1]
        
        if final_plate.size > 0:
            detected = reader.readtext(final_plate, paragraph=True, x_ths=2.0)
            
            for (bbox, raw_text) in detected:
                plate_list.append(raw_text)
    
    else:
      
        empty_frame_count += 1
        if empty_frame_count > 30:
            plate_list.clear()
            
    return get_best_plate(plate_list)