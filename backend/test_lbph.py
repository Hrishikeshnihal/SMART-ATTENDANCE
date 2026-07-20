import cv2
import numpy as np

try:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    print("LBPH loaded successfully")
except Exception as e:
    print(f"Error: {e}")
