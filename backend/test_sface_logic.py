import cv2
import numpy as np
import os

models_dir = os.path.join('static', 'models')
yunet_path = os.path.join(models_dir, "face_detection_yunet_2023mar.onnx")
sface_path = os.path.join(models_dir, "face_recognition_sface_2021dec.onnx")

img = np.ones((480, 640, 3), dtype=np.uint8) * 100
student_img = np.ones((200, 200, 3), dtype=np.uint8) * 100

height, width, _ = img.shape
detector = cv2.FaceDetectorYN.create(yunet_path, "", (width, height))
recognizer = cv2.FaceRecognizerSF.create(sface_path, "")

_, faces = detector.detect(img)
faces_in_classroom = faces if faces is not None else []
print(f"Faces in classroom: {len(faces_in_classroom)}")

s_h, s_w, _ = student_img.shape
detector.setInputSize((s_w, s_h))
_, s_faces = detector.detect(student_img)
s_faces = s_faces if s_faces is not None else []
print(f"Student faces: {len(s_faces)}")

if len(s_faces) > 0:
    s_face = s_faces[0]
    s_aligned = recognizer.alignCrop(student_img, s_face)
    s_feature = recognizer.feature(s_aligned)
    print("Feature extracted")
