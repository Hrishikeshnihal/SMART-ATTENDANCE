import urllib.request
import os
import cv2

models_dir = 'static/models'
os.makedirs(models_dir, exist_ok=True)

yunet_url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
sface_url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

yunet_path = os.path.join(models_dir, "face_detection_yunet_2023mar.onnx")
sface_path = os.path.join(models_dir, "face_recognition_sface_2021dec.onnx")

print("Downloading YuNet (Detector)...")
if not os.path.exists(yunet_path):
    urllib.request.urlretrieve(yunet_url, yunet_path)

print("Downloading SFace (Recognizer)...")
if not os.path.exists(sface_path):
    urllib.request.urlretrieve(sface_url, sface_path)

print("Models downloaded.")

try:
    detector = cv2.FaceDetectorYN.create(yunet_path, "", (320, 320))
    recognizer = cv2.FaceRecognizerSF.create(sface_path, "")
    print("SUCCESS: YuNet and SFace loaded successfully via OpenCV DNN!")
except Exception as e:
    print(f"FAILED to load: {e}")
