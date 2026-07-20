from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import base64
import datetime
import jwt
from functools import wraps

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'super_secret_jwt_key_123'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2:
                token = parts[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            conn = get_db_connection()
            current_user = conn.execute('SELECT * FROM users WHERE id = ?', (data['user_id'],)).fetchone()
            conn.close()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
            
        return f(dict(current_user), *args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                        (username, password)).fetchone()
    conn.close()
    
    if user:
        token = jwt.encode({
            'user_id': user['id'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'subject': user['subject']
            }
        })
    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # SECURITY FIX: Only allow registering as 'student' from the public signup
    # Teachers and Admins must be created by the Admin dashboard.
    role = 'student' 
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                     (username, password, role))
        conn.commit()
        return jsonify({'message': 'Student account created successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 400
    finally:
        conn.close()

@app.route('/api/admin/dashboard', methods=['GET'])
@token_required
def admin_dashboard(current_user):
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    users = [dict(row) for row in conn.execute('SELECT id, username, role, subject FROM users').fetchall()]
    logs = [dict(row) for row in conn.execute('''
        SELECT users.username, attendance.status, attendance.date, attendance.subject 
        FROM attendance 
        JOIN users ON attendance.student_id = users.id 
        ORDER BY date DESC
    ''').fetchall()]
    conn.close()
    
    return jsonify({'users': users, 'logs': logs})

@app.route('/api/admin/create_teacher', methods=['POST'])
@token_required
def create_teacher(current_user):
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.json
    username = data.get('username')
    password = data.get('password')
    subject = data.get('subject')
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password, role, subject) VALUES (?, ?, ?, ?)', 
                     (username, password, 'teacher', subject))
        conn.commit()
        return jsonify({'message': 'Teacher created successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 400
    finally:
        conn.close()

@app.route('/api/admin/delete_user/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User deleted'})

@app.route('/api/admin/assign_subject/<int:user_id>', methods=['PUT'])
@token_required
def assign_subject(current_user, user_id):
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
        
    subject = request.json.get('subject')
    conn = get_db_connection()
    conn.execute('UPDATE users SET subject = ? WHERE id = ?', (subject, user_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Subject assigned'})

@app.route('/api/teacher/dashboard', methods=['GET'])
@token_required
def teacher_dashboard(current_user):
    if current_user['role'] != 'teacher':
        return jsonify({'message': 'Unauthorized'}), 403
        
    subject = current_user['subject']
    if not subject:
        return jsonify({'error': 'No subject assigned. Contact Admin.'}), 403
        
    selected_date = request.args.get('date', datetime.date.today().strftime("%Y-%m-%d"))
    
    conn = get_db_connection()
    all_students = conn.execute('SELECT id, username FROM users WHERE role = "student"').fetchall()
    
    attendance_records = conn.execute('''
        SELECT student_id, status 
        FROM attendance 
        WHERE date = ? AND subject = ?
    ''', (selected_date, subject)).fetchall()
    
    attendance_map = {row['student_id']: row['status'] for row in attendance_records}
    
    logs = []
    for student in all_students:
        status = attendance_map.get(student['id'], 'Absent')
        logs.append({
            'student_id': student['id'],
            'username': student['username'],
            'date': selected_date,
            'status': status
        })
    
    total_students = len(all_students)
    total_lectures = conn.execute('SELECT COUNT(DISTINCT date) FROM attendance WHERE subject = ?', (subject,)).fetchone()[0]
    today_present = len(attendance_records)
    
    conn.close()
    
    return jsonify({
        'subject': subject,
        'logs': logs,
        'stats': {
            'total_students': total_students,
            'total_lectures': total_lectures,
            'today_present': today_present
        }
    })

@app.route('/api/teacher/manual_mark', methods=['POST'])
@token_required
def manual_mark(current_user):
    if current_user['role'] != 'teacher':
        return jsonify({'message': 'Unauthorized'}), 403
        
    subject = current_user['subject']
    if not subject:
        return jsonify({'error': 'No subject assigned'}), 403
        
    data = request.json
    student_id = data.get('student_id')
    date = data.get('date')
    
    conn = get_db_connection()
    exists = conn.execute('SELECT id FROM attendance WHERE student_id = ? AND date = ? AND subject = ?', 
                          (student_id, date, subject)).fetchone()
    if not exists:
        conn.execute('INSERT INTO attendance (date, student_id, subject, status) VALUES (?, ?, ?, ?)', 
                     (date, student_id, subject, 'Present'))
        conn.commit()
    conn.close()
    
    return jsonify({'message': 'Marked present'})

@app.route('/api/student/dashboard', methods=['GET'])
@token_required
def student_dashboard(current_user):
    if current_user['role'] != 'student':
        return jsonify({'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    user = conn.execute('SELECT face_image_path FROM users WHERE id = ?', (current_user['id'],)).fetchone()
    face_registered = bool(user['face_image_path'])
    
    teacher_subjects = conn.execute('SELECT DISTINCT subject FROM users WHERE role="teacher" AND subject IS NOT NULL').fetchall()
    subjects = [row['subject'] for row in teacher_subjects]
    
    student_stats = []
    for sub in subjects:
        total_lec = conn.execute('SELECT COUNT(DISTINCT date) FROM attendance WHERE subject = ?', (sub,)).fetchone()[0]
        attended = conn.execute('SELECT COUNT(*) FROM attendance WHERE student_id = ? AND subject = ?', (current_user['id'], sub)).fetchone()[0]
        missed = max(0, total_lec - attended)
        
        if total_lec > 0:
            perc = round((attended / total_lec) * 100, 1)
        else:
            perc = 100.0
            
        student_stats.append({
            'subject': sub,
            'total': total_lec,
            'attended': attended,
            'missed': missed,
            'percentage': perc
        })
        
    conn.close()
    return jsonify({
        'face_registered': face_registered,
        'stats': student_stats
    })

@app.route('/api/student/register_face', methods=['POST'])
@token_required
def register_face(current_user):
    if current_user['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    image_data = data.get('image')
    if not image_data:
        return jsonify({'error': 'No image provided'}), 400
        
    encoded_data = image_data.split(',')[1]
    nparr = base64.b64decode(encoded_data)
    
    file_path = os.path.join(UPLOAD_FOLDER, f"student_{current_user['id']}.jpg")
    with open(file_path, "wb") as fh:
        fh.write(nparr)
        
    conn = get_db_connection()
    conn.execute('UPDATE users SET face_image_path = ? WHERE id = ?', (file_path, current_user['id']))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Face registered successfully'})

@app.route('/api/teacher/mark_attendance', methods=['POST'])
@token_required
def mark_attendance(current_user):
    if current_user['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
        
    subject = current_user['subject']
    if not subject:
        return jsonify({'error': 'No subject assigned'}), 403
        
    data = request.json
    image_data = data.get('image')
    if not image_data:
        return jsonify({'error': 'No image provided'}), 400
        
    encoded_data = image_data.split(',')[1]
    nparr = base64.b64decode(encoded_data)
    
    temp_path = os.path.join(UPLOAD_FOLDER, "temp_classroom.jpg")
    with open(temp_path, "wb") as fh:
        fh.write(nparr)
        
    conn = get_db_connection()
    students = [dict(row) for row in conn.execute('SELECT id, face_image_path, username FROM users WHERE role = "student" AND face_image_path IS NOT NULL').fetchall()]
    
    recognized_students = []
    
    import cv2
    import numpy as np
    
    models_dir = os.path.join('static', 'models')
    yunet_path = os.path.join(models_dir, "face_detection_yunet_2023mar.onnx")
    sface_path = os.path.join(models_dir, "face_recognition_sface_2021dec.onnx")
    
    if os.path.exists(yunet_path) and os.path.exists(sface_path):
        img = cv2.imread(temp_path)
        if img is not None:
            height, width, _ = img.shape
            detector = cv2.FaceDetectorYN.create(yunet_path, "", (width, height))
            recognizer = cv2.FaceRecognizerSF.create(sface_path, "")
            
            _, faces = detector.detect(img)
            faces_in_classroom = faces if faces is not None else []
            
            for student in students:
                match_found = False
                s_img = cv2.imread(student['face_image_path'])
                
                if s_img is not None and len(faces_in_classroom) > 0:
                    s_h, s_w, _ = s_img.shape
                    detector.setInputSize((s_w, s_h))
                    _, s_faces = detector.detect(s_img)
                    
                    if s_faces is not None and len(s_faces) > 0:
                        s_face = s_faces[0]
                        s_aligned = recognizer.alignCrop(s_img, s_face)
                        s_feature = recognizer.feature(s_aligned)
                        
                        detector.setInputSize((width, height)) 
                        
                        for c_face in faces_in_classroom:
                            c_aligned = recognizer.alignCrop(img, c_face)
                            c_feature = recognizer.feature(c_aligned)
                            
                            score = recognizer.match(s_feature, c_feature, cv2.FaceRecognizerSF_FR_COSINE)
                            if score >= 0.363:
                                match_found = True
                                break
                                
                if match_found and not any(rs['id'] == student['id'] for rs in recognized_students):
                    recognized_students.append(student)
                    
    today = datetime.date.today().strftime("%Y-%m-%d")
    for student in recognized_students:
        exists = conn.execute('SELECT id FROM attendance WHERE student_id = ? AND date = ? AND subject = ?', 
                              (student['id'], today, subject)).fetchone()
        if not exists:
            conn.execute('INSERT INTO attendance (date, student_id, subject, status) VALUES (?, ?, ?, ?)', 
                         (today, student['id'], subject, 'Present'))
            
    conn.commit()
    conn.close()
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    names = [s['username'] for s in recognized_students]
    return jsonify({
        'success': True, 
        'message': f"Attendance marked for: {', '.join(names) if names else 'No one recognized'}"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
