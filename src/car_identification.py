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
    """
    Returns the most common plate seen in the last few frames.
    Validates that the result has BOTH letters and numbers.
    """
    clean_votes = []
    
    for raw_line in current_list:
        # 1. Basic Cleanup
        text = raw_line.split(":")[1] if "Full Plate:" in raw_line else raw_line
        
        # Keep only Alphanumeric (A-Z, 0-9)
        clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())

        # 2. STRICT CONTENT VALIDATION
        # Must have at least one Letter AND at least one Number
        has_letter = bool(re.search(r'[A-Z]', clean_text))
        has_number = bool(re.search(r'[0-9]', clean_text))
        
        if len(clean_text) >= 3 and has_letter and has_number:
            clean_votes.append(clean_text)

    if not clean_votes:
        return None

    vote_counts = Counter(clean_votes)
    winner, count = vote_counts.most_common(1)[0]
    
    # Require confirmation count (adjust to 2 or 3 as needed)
    if count < 2:
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
    
    final_location = None
    plate_found_in_this_frame = False

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        apprx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)
        
        # 1. GEOMETRY CHECK: Must have 4 corners
        if len(apprx) == 4:
            
            # 2. LOOSE ASPECT RATIO CHECK
            # We relax this to 0.6 to allow square/vertical plates if they have text.
            # But we still reject thin strips (like chair legs) which are usually < 0.3
            (x, y, w, h) = cv2.boundingRect(apprx)
            aspect_ratio = w / float(h)
            
            if aspect_ratio < 0.6: 
                continue 

            # 3. EXTRACTION
            msk = np.zeros(gray.shape, np.uint8)
            cv2.drawContours(msk, [apprx], 0, 255, -1)
            (x, y) = np.where(msk == 255)
            
            if len(x) == 0 or len(y) == 0: continue
            
            (x1, y1) = (np.min(x), np.min(y))
            (x2, y2) = (np.max(x), np.max(y))
            candidate_plate = gray[x1:x2 + 1, y1:y2 + 1]
            
            # Check for decent size to avoid OCR on noise
            if candidate_plate.size < 500: 
                continue

            # 4. OCR CHECK
            detected = reader.readtext(candidate_plate, paragraph=True, x_ths=2.0)
            
            valid_candidate = False
            for (bbox, raw_text) in detected:
                clean_text = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
                
                # 5. THE "MAGIC" LOGIC
                # "Must contain a number AND an alphabet regardless of orientation"
                has_letter = bool(re.search(r'[A-Z]', clean_text))
                has_number = bool(re.search(r'[0-9]', clean_text))
                
                # Length > 2 ensures we don't pick up "1A" if that's too short for you
                if len(clean_text) >= 2 and has_letter and has_number:
                    plate_list.append(raw_text)
                    valid_candidate = True
            
            # Only draw the box if we found the valid text
            if valid_candidate:
                final_location = apprx
                plate_found_in_this_frame = True
                empty_frame_count = 0
                break 

    if not plate_found_in_this_frame:
        empty_frame_count += 1
        if empty_frame_count > 30:
            plate_list.clear()

    return get_best_plate(plate_list), final_location