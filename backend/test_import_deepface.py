import sys
try:
    from deepface import DeepFace
    print("SUCCESS: deepface imported")
except Exception as e:
    print(f"FAILED: {e}")
