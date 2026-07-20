import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../AuthContext';
import { Users, BookOpen, UserCheck, Camera, Search } from 'lucide-react';

const TeacherDashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [message, setMessage] = useState('');
  const [facingMode, setFacingMode] = useState('user');
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    fetchDashboard();
    return () => stopCamera();
  }, [date]);

  useEffect(() => {
    if (isCapturing && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(e => console.error('Video play error:', e));
    }
  }, [isCapturing]);

  const fetchDashboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/teacher/dashboard?date=${date}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || json.message || 'Failed to fetch data');
      setData(json);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  };

  const startCamera = async () => {
    stopCamera();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCapturing(true);
    } catch (err) {
      setError('Camera access denied or device not found.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCapturing(false);
  };

  const switchCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
    setTimeout(startCamera, 100);
  };

  const takeAttendance = async () => {
    if (!videoRef.current) return;
    
    setMessage('Analyzing classroom with AI... Please wait.');
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext('2d').drawImage(videoRef.current, 0, 0);
    const imageBase64 = canvas.toDataURL('image/jpeg');
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/teacher/mark_attendance', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ image: imageBase64 })
      });
      const json = await res.json();
      if (res.ok) {
        setMessage(json.message);
        setTimeout(() => {
          setMessage('');
          stopCamera();
          fetchDashboard();
        }, 2000);
      } else {
        setMessage('');
        setError(json.error || 'Failed to mark attendance');
      }
    } catch (err) {
      setError('Error connecting to AI Server.');
      setMessage('');
    }
  };

  const manualMarkPresent = async (studentId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/teacher/manual_mark', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ student_id: studentId, date })
      });
      if (res.ok) fetchDashboard();
    } catch (err) {
      console.error(err);
    }
  };

  if (error && !data) return <div className="container animate-fade-in"><div className="badge badge-danger p-4" style={{display: 'block', fontSize: '1rem', padding: '1rem'}}>{error}</div></div>;
  if (!data) return <div className="container">Loading...</div>;

  return (
    <div className="animate-fade-in" style={{ padding: '2rem 0' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1>Professor {user.username}</h1>
        <p>{data.subject} - Faculty Administration Dashboard</p>
      </header>
      
      {error && <div className="badge badge-danger" style={{ display: 'block', marginBottom: '1rem', padding: '0.75rem' }}>{error}</div>}

      <div className="grid grid-cols-3" style={{ marginBottom: '2rem' }}>
        <div className="glass-card stat-card">
          <BookOpen size={24} style={{ color: 'var(--primary)', margin: '0 auto 0.5rem' }} />
          <h3>Total Lectures</h3>
          <p className="value">{data.stats.total_lectures}</p>
        </div>
        <div className="glass-card stat-card" style={{ borderTopColor: 'var(--accent)' }}>
          <Users size={24} style={{ color: 'var(--accent)', margin: '0 auto 0.5rem' }} />
          <h3>Total Students</h3>
          <p className="value">{data.stats.total_students}</p>
        </div>
        <div className="glass-card stat-card" style={{ borderTopColor: 'var(--success)' }}>
          <UserCheck size={24} style={{ color: 'var(--success)', margin: '0 auto 0.5rem' }} />
          <h3>Present Today</h3>
          <p className="value">{data.stats.today_present}</p>
        </div>
      </div>

      <div className="glass-card" style={{ marginBottom: '2rem', textAlign: 'center' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          <Camera size={24} /> Live AI Attendance Capture
        </h2>
        <p style={{ marginBottom: '1.5rem' }}>Point the camera at the classroom to instantly record attendance for all recognized students.</p>
        
        {!isCapturing ? (
          <button className="btn" onClick={startCamera}>Turn on Classroom Camera</button>
        ) : (
          <div>
            <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', maxWidth: '600px', borderRadius: '12px', marginBottom: '1rem', border: '2px solid var(--primary)', transform: facingMode === 'user' ? 'scaleX(-1)' : 'none' }}></video>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button className="btn btn-secondary" onClick={switchCamera}>🔄 Flip Camera</button>
              <button className="btn btn-secondary" onClick={stopCamera}>Cancel</button>
              <button className="btn" style={{ background: 'var(--success)' }} onClick={takeAttendance}>Capture & Mark Attendance</button>
            </div>
          </div>
        )}
        {message && <div style={{ marginTop: '1rem', color: 'var(--success)', fontWeight: 'bold' }}>{message}</div>}
      </div>

      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2>Classroom Attendance Roster</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label style={{ color: 'var(--text-muted)' }}>Date:</label>
            <input 
              type="date" 
              value={date} 
              onChange={(e) => setDate(e.target.value)}
              style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderRadius: '6px', padding: '0.5rem', color: 'var(--text-main)', colorScheme: 'dark' }}
            />
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Student Name</th>
                <th>Date</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {data.logs.map((log, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: '500' }}>{log.username}</td>
                  <td>{log.date}</td>
                  <td>
                    <span className={`badge ${log.status === 'Present' ? 'badge-success' : 'badge-danger'}`}>
                      {log.status}
                    </span>
                  </td>
                  <td>
                    {log.status === 'Absent' ? (
                      <button onClick={() => manualMarkPresent(log.student_id)} className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>
                        Mark Present
                      </button>
                    ) : (
                      <span style={{ color: 'var(--success)', fontSize: '0.875rem', fontWeight: '500' }}>✓ Recorded</span>
                    )}
                  </td>
                </tr>
              ))}
              {data.logs.length === 0 && (
                <tr><td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No students found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;
