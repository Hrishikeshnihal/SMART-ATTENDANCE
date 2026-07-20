import sqlite3
import os

DB_NAME = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Drop existing tables for the schema upgrade
    cursor.execute('DROP TABLE IF EXISTS attendance')
    cursor.execute('DROP TABLE IF EXISTS users')
    
    # Create Users table (added subject)
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            subject TEXT,
            face_image_path TEXT
        )
    ''')
    
    # Create Attendance table (added subject)
    cursor.execute('''
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES users(id)
        )
    ''')
    
    # Insert 5 teachers and admin
    cursor.execute("INSERT INTO users (username, password, role, subject) VALUES ('admin', 'admin123', 'admin', NULL)")
    cursor.execute("INSERT INTO users (username, password, role, subject) VALUES ('teacher1', 'pass123', 'teacher', 'EM-2')")
    cursor.execute("INSERT INTO users (username, password, role, subject) VALUES ('teacher2', 'pass123', 'teacher', 'Engineering Physics')")
    cursor.execute("INSERT INTO users (username, password, role, subject) VALUES ('teacher3', 'pass123', 'teacher', 'DSDA')")
    cursor.execute("INSERT INTO users (username, password, role, subject) VALUES ('teacher4', 'pass123', 'teacher', 'FCSN')")
    cursor.execute("INSERT INTO users (username, password, role, subject) VALUES ('teacher5', 'pass123', 'teacher', 'FCPP')")
    cursor.execute("INSERT INTO users (username, password, role, subject) VALUES ('student1', 'pass123', 'student', NULL)")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # If the DB already exists, we might need to delete it so the new schema applies for beginners
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("Old database removed.")
        
    init_db()
    print("New Database initialized successfully with Attendance tracking!")
