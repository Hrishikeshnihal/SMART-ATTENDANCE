import cv2
import numpy as np

recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Generate dummy faces (different sizes)
img1 = np.ones((200, 200), dtype=np.uint8) * 100
img2 = np.ones((150, 150), dtype=np.uint8) * 100

try:
    recognizer.train([img1], np.array([0]))
    label, conf = recognizer.predict(img2)
    print("Predicted label:", label, "Confidence:", conf)
except Exception as e:
    print("Error:", e)
