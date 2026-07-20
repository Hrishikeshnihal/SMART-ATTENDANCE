from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import base64
import datetime
# import cv2
# from deepface import DeepFace  # Commented out temporarily for quick startup

app = Flask(__name__)
app.secret_key = 'super_secret_key'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['subject'] = user['subject']
            
            if user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password!')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        subject = request.form.get('subject') # Optional from form
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, role, subject) VALUES (?, ?, ?, ?)', 
                         (username, password, role, subject))
            conn.commit()
            flash('Account created successfully! You can now log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists! Please choose another one.')
        finally:
            conn.close()
            
    return render_template('signup.html')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    logs = conn.execute('''
        SELECT users.username, attendance.status, attendance.date, attendance.subject
        FROM attendance 
        JOIN users ON attendance.student_id = users.id 
        ORDER BY date DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', users=users, logs=logs)

@app.route('/delete_user/<int:id>')
def delete_user(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/assign_subject/<int:id>', methods=['POST'])
def assign_subject(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    subject = request.form.get('subject')
    conn = get_db_connection()
    conn.execute('UPDATE users SET subject = ? WHERE id = ?', (subject, id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/teacher-dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    subject = session.get('subject')
    if not subject:
        return "Access Denied: You must be assigned a subject by the admin before you can access the teacher portal.", 403
        
    selected_date = request.args.get('date', datetime.date.today().strftime("%Y-%m-%d"))
    
    # Get all students
    all_students = conn.execute('SELECT id, username FROM users WHERE role = "student"').fetchall()
    
    # Get attendance for selected date
    attendance_records = conn.execute('''
        SELECT student_id, status 
        FROM attendance 
        WHERE date = ? AND subject = ?
    ''', (selected_date, subject)).fetchall()
    
    # Map student_id to status
    attendance_map = {row['student_id']: row['status'] for row in attendance_records}
    
    # Build complete roster
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
    
    return render_template('teacher_dashboard.html', 
                           username=session['username'], 
                           subject=subject,
                           logs=logs,
                           selected_date=selected_date,
                           total_students=total_students,
                           total_lectures=total_lectures,
                           today_present=today_present)

@app.route('/manual_mark_present/<int:student_id>/<date>', methods=['POST'])
def manual_mark_present(student_id, date):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
        
    subject = session.get('subject')
    if not subject:
        return "Access Denied: No subject assigned.", 403
        
    conn = get_db_connection()
    
    exists = conn.execute('SELECT id FROM attendance WHERE student_id = ? AND date = ? AND subject = ?', 
                          (student_id, date, subject)).fetchone()
    if not exists:
        conn.execute('INSERT INTO attendance (date, student_id, subject, status) VALUES (?, ?, ?, ?)', 
                     (date, student_id, subject, 'Present'))
        conn.commit()
    conn.close()
    
    return redirect(url_for('teacher_dashboard', date=date))

@app.route('/student-dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    user = conn.execute('SELECT face_image_path FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    face_registered = bool(user['face_image_path'])
    
    # Fetch all dynamic subjects that have been assigned to teachers
    teacher_subjects = conn.execute('SELECT DISTINCT subject FROM users WHERE role="teacher" AND subject IS NOT NULL').fetchall()
    subjects = [row['subject'] for row in teacher_subjects]
    
    student_stats = []
    
    for sub in subjects:
        total_lec = conn.execute('SELECT COUNT(DISTINCT date) FROM attendance WHERE subject = ?', (sub,)).fetchone()[0]
        attended = conn.execute('SELECT COUNT(*) FROM attendance WHERE student_id = ? AND subject = ?', (session['user_id'], sub)).fetchone()[0]
        missed = max(0, total_lec - attended)
        
        if total_lec > 0:
            perc = round((attended / total_lec) * 100, 1)
        else:
            perc = 100.0  # Avoid showing 0% when no lectures have happened

        
        student_stats.append({
            'subject': sub,
            'total': total_lec,
            'attended': attended,
            'missed': missed,
            'percentage': perc
        })
        
    conn.close()
    
    return render_template('student_dashboard.html', 
                           username=session['username'], 
                           student_stats=student_stats,
                           face_registered=face_registered)

@app.route('/register_face', methods=['POST'])
def register_face():
    if 'user_id' not in session or session['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    image_data = data['image']
    
    encoded_data = image_data.split(',')[1]
    nparr = base64.b64decode(encoded_data)
    
    file_path = os.path.join(UPLOAD_FOLDER, f"student_{session['user_id']}.jpg")
    with open(file_path, "wb") as fh:
        fh.write(nparr)
        
    conn = get_db_connection()
    conn.execute('UPDATE users SET face_image_path = ? WHERE id = ?', (file_path, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Face registered successfully!'})

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
        
    if not session.get('subject'):
        return jsonify({'error': 'No subject assigned to this teacher.'}), 403
        
    data = request.json
    image_data = data['image']
    
    encoded_data = image_data.split(',')[1]
    nparr = base64.b64decode(encoded_data)
    
    temp_path = os.path.join(UPLOAD_FOLDER, "temp_classroom.jpg")
    with open(temp_path, "wb") as fh:
        fh.write(nparr)
        
    conn = get_db_connection()
    students = conn.execute('SELECT id, face_image_path, username FROM users WHERE role = "student" AND face_image_path IS NOT NULL').fetchall()
    
    recognized_students = []
    
    # Try to use REAL AI if we are on the local laptop with enough RAM
    try:
        from deepface import DeepFace
        real_ai_available = True
    except ImportError:
        real_ai_available = False

    if real_ai_available:
        try:
            # GROUP PHOTO UPGRADE: Extract all faces from the classroom image ONCE
            faces_in_classroom = DeepFace.extract_faces(img_path=temp_path, enforce_detection=True)
        except Exception as e:
            # If no faces are detected, DeepFace throws an exception
            faces_in_classroom = []

        for student in students:
            match_found = False
            # Loop through the extracted faces
            for classroom_face in faces_in_classroom:
                try:
                    # Compare the student's registered face against the extracted face array
                    result = DeepFace.verify(img1_path=student['face_image_path'], img2_path=classroom_face['face'], enforce_detection=False)
                    if result['verified']:
                        match_found = True
                        break # Found them in the crowd!
                except:
                    pass
            if match_found:
                recognized_students.append(student)
                
    else:
        # HIGH-ACCURACY OPENCV SFACE (DEEP LEARNING ONNX)
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
                
                # Detect faces in classroom
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
                            # Align and extract feature for student
                            s_aligned = recognizer.alignCrop(s_img, s_face)
                            s_feature = recognizer.feature(s_aligned)
                            
                            detector.setInputSize((width, height)) # reset for classroom faces
                            
                            for c_face in faces_in_classroom:
                                # Align and extract feature for classroom face
                                c_aligned = recognizer.alignCrop(img, c_face)
                                c_feature = recognizer.feature(c_aligned)
                                
                                # Calculate cosine similarity (1.0 is exact match, >= 0.363 is same person)
                                score = recognizer.match(s_feature, c_feature, cv2.FaceRecognizerSF_FR_COSINE)
                                if score >= 0.363:
                                    match_found = True
                                    break
                                    
                    if match_found and not any(rs['id'] == student['id'] for rs in recognized_students):
                        recognized_students.append(student)
            
    for student in recognized_students:
        today = datetime.date.today().strftime("%Y-%m-%d")
        exists = conn.execute('SELECT id FROM attendance WHERE student_id = ? AND date = ? AND subject = ?', 
                              (student['id'], today, session['subject'])).fetchone()
        if not exists:
            conn.execute('INSERT INTO attendance (date, student_id, subject, status) VALUES (?, ?, ?, ?)', 
                         (today, student['id'], session['subject'], 'Present'))
            
    conn.commit()
    conn.close()
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    names = [s['username'] for s in recognized_students]
    
    return jsonify({
        'success': True, 
        'message': f"Attendance marked for: {', '.join(names) if names else 'No one recognized'}"
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
