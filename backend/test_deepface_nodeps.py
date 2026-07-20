import sys
try:
    from deepface import DeepFace
    print("Deepface imported successfully")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

import cv2
import numpy as np

img1 = np.zeros((100, 100, 3), dtype=np.uint8)
img2 = np.zeros((100, 100, 3), dtype=np.uint8)

try:
    res = DeepFace.verify(img1_path=img1, img2_path=img2, model_name="SFace", detector_backend="opencv", enforce_detection=False)
    print("Verify result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
