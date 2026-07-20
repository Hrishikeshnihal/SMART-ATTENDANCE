import urllib.request
import urllib.parse
from http.cookiejar import CookieJar
import json
import base64

# Create a dummy image
import cv2
import numpy as np
dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
_, buffer = cv2.imencode('.jpg', dummy_img)
b64_str = base64.b64encode(buffer).decode('utf-8')
data_url = "data:image/jpeg;base64," + b64_str

cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Login as teacher1
data = urllib.parse.urlencode({'username': 'teacher1', 'password': 'pass123'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:5000/login', data=data)
opener.open(req)

# Mark attendance
req = urllib.request.Request(
    'http://127.0.0.1:5000/mark_attendance', 
    data=json.dumps({'image': data_url}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
try:
    response = opener.open(req)
    print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
