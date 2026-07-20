import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../AuthContext';
import { Camera, CheckCircle } from 'lucide-react';

const StudentDashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [message, setMessage] = useState('');
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    fetchDashboard();
    return () => stopCamera();
  }, []);

  useEffect(() => {
    if (isRegistering && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(e => console.error('Video play error:', e));
    }
  }, [isRegistering]);

  const fetchDashboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/student/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.message || 'Failed to fetch data');
      setData(json);
    } catch (err) {
      setError(err.message);
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
      streamRef.current = stream;
      setIsRegistering(true);
    } catch (err) {
      setError('Camera access denied. Please allow camera permissions.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsRegistering(false);
  };

  const registerFace = async () => {
    if (!videoRef.current) return;
    
    setMessage('Processing...');
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext('2d').drawImage(videoRef.current, 0, 0);
    const imageBase64 = canvas.toDataURL('image/jpeg');
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/student/register_face', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ image: imageBase64 })
      });
      const json = await res.json();
      if (res.ok) {
        setMessage('Face registered successfully!');
        stopCamera();
        fetchDashboard(); // Refresh to update face_registered status
      } else {
        setMessage('');
        setError(json.error || 'Failed to register face');
      }
    } catch (err) {
      setError('Error connecting to server.');
      setMessage('');
    }
  };

  if (error) return <div className="container animate-fade-in"><div className="badge badge-danger p-4">{error}</div></div>;
  if (!data) return <div className="container">Loading...</div>;

  return (
    <div className="animate-fade-in" style={{ padding: '2rem 0' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1>Welcome, {user.username}</h1>
        <p>Student Academic Portal - Track your attendance across all subjects</p>
      </header>

      {!data.face_registered && (
        <div className="glass-card" style={{ marginBottom: '2rem', textAlign: 'center', borderColor: 'var(--secondary)' }}>
          <h2 style={{ color: 'var(--secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            <Camera size={24} /> Initial Face Registration Required
          </h2>
          <p style={{ marginBottom: '1.5rem' }}>Please register your face once for the AI attendance system to recognize you in classes.</p>
          
          {!isRegistering ? (
            <button className="btn" onClick={startCamera}>Turn on Camera</button>
          ) : (
            <div>
              <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', maxWidth: '400px', borderRadius: '12px', marginBottom: '1rem', border: '2px solid var(--primary)' }}></video>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                <button className="btn btn-secondary" onClick={stopCamera}>Cancel</button>
                <button className="btn" style={{ background: 'var(--success)' }} onClick={registerFace}>Capture & Register</button>
              </div>
            </div>
          )}
          {message && <div style={{ marginTop: '1rem', color: 'var(--success)', fontWeight: 'bold' }}>{message}</div>}
        </div>
      )}

      {data.face_registered && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)', marginBottom: '2rem', background: 'rgba(16, 185, 129, 0.1)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <CheckCircle size={20} />
          <span style={{ fontWeight: '500' }}>Face Registration Active. Ready for AI Attendance.</span>
        </div>
      )}

      <div className="grid grid-cols-2">
        {data.stats.map((stat, idx) => {
          let statusColor = 'var(--success)';
          if (stat.percentage < 50) statusColor = 'var(--danger)';
          else if (stat.percentage < 75) statusColor = '#f59e0b'; // warning orange

          return (
            <div key={idx} className="glass-card">
              <h2 style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>{stat.subject}</h2>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '1.5rem' }}>
                <div>
                  <p style={{ fontSize: '0.875rem' }}>Total Lectures: <strong style={{ color: 'var(--text-main)' }}>{stat.total}</strong></p>
                  <p style={{ fontSize: '0.875rem' }}>Attended: <strong style={{ color: 'var(--text-main)' }}>{stat.attended}</strong></p>
                  <p style={{ fontSize: '0.875rem' }}>Missed: <strong style={{ color: 'var(--text-main)' }}>{stat.missed}</strong></p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '2.5rem', fontWeight: '700', color: statusColor, lineHeight: '1' }}>
                    {stat.percentage}%
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '1.5rem', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '999px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${stat.percentage}%`, background: statusColor, transition: 'width 1s ease' }}></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StudentDashboard;
