import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

# Setup cookie jar to maintain session
cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Login as student1
data = urllib.parse.urlencode({'username': 'student1', 'password': 'pass123'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:5000/login', data=data)
try:
    response = opener.open(req)
    print(f"Student login success: {response.geturl()}")
except Exception as e:
    print(f"Student login error: {e}")

# Login as teacher1
data = urllib.parse.urlencode({'username': 'teacher1', 'password': 'pass123'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:5000/login', data=data)
try:
    response = opener.open(req)
    print(f"Teacher login success: {response.geturl()}")
except Exception as e:
    print(f"Teacher login error: {e}")
