import cv2
import numpy as np

try:
    print("Cascade path:", cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    print("Cascade loaded:", not face_cascade.empty())
    
    # create dummy image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
    print("Faces detected:", len(faces))
except Exception as e:
    import traceback
    traceback.print_exc()
