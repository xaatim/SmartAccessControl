import cv2 
import easyocr
from typing import Callable

def IdentifyCar(frame):
  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  filter = cv2.bilateralFilter(gray, 11, 17, 17)
  edge = cv2.Canny(filter, 30, 200)
  cv2.imshow("filterFrame",filter)
  cv2.imshow("greyFrame",gray)
  cv2.imshow("edgeFrame",edge)
  


