import React, { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { Settings, UserPlus, Trash2, Edit2 } from 'lucide-react';

const AdminDashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState({ users: [], logs: [] });
  const [error, setError] = useState('');
  
  // Teacher Creation Form
  const [newTeacher, setNewTeacher] = useState({ username: '', password: '', subject: '' });
  const [msg, setMsg] = useState('');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/admin/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.message || 'Failed to fetch data');
      setData(json);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateTeacher = async (e) => {
    e.preventDefault();
    setMsg('');
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/admin/create_teacher', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newTeacher)
      });
      const json = await res.json();
      if (res.ok) {
        setMsg(json.message);
        setNewTeacher({ username: '', password: '', subject: '' });
        fetchDashboard();
      } else {
        setError(json.message || 'Failed to create teacher');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (id) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/admin/delete_user/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) fetchDashboard();
    } catch (err) {
      console.error(err);
    }
  };

  const handleAssignSubject = async (id, subject) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/admin/assign_subject/${id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ subject })
      });
      if (res.ok) fetchDashboard();
    } catch (err) {
      console.error(err);
    }
  };

  if (error && data.users.length === 0) return <div className="container animate-fade-in"><div className="badge badge-danger p-4">{error}</div></div>;

  return (
    <div className="animate-fade-in" style={{ padding: '2rem 0' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Settings size={32} /> Admin Dashboard</h1>
        <p>System Management and Global Attendance Records</p>
      </header>

      {error && <div className="badge badge-danger" style={{ display: 'block', marginBottom: '1rem', padding: '0.75rem' }}>{error}</div>}
      {msg && <div className="badge badge-success" style={{ display: 'block', marginBottom: '1rem', padding: '0.75rem' }}>{msg}</div>}

      <div className="grid grid-cols-2" style={{ marginBottom: '2rem' }}>
        <div className="glass-card">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><UserPlus size={20} /> Create Teacher Account</h2>
          <form onSubmit={handleCreateTeacher} style={{ marginTop: '1.5rem' }}>
            <div className="input-group">
              <label>Username</label>
              <input type="text" required value={newTeacher.username} onChange={e => setNewTeacher({...newTeacher, username: e.target.value})} />
            </div>
            <div className="input-group">
              <label>Password</label>
              <input type="password" required value={newTeacher.password} onChange={e => setNewTeacher({...newTeacher, password: e.target.value})} />
            </div>
            <div className="input-group">
              <label>Assigned Subject</label>
              <input type="text" required value={newTeacher.subject} onChange={e => setNewTeacher({...newTeacher, subject: e.target.value})} placeholder="e.g. Physics" />
            </div>
            <button type="submit" className="btn">Create Teacher</button>
          </form>
        </div>
      </div>

      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <h2>User Management</h2>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Role</th>
                <th>Subject (Teachers)</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {data.users.map(u => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td style={{ fontWeight: '500' }}>{u.username}</td>
                  <td>
                    <span className={`badge ${u.role === 'admin' ? 'badge-danger' : u.role === 'teacher' ? 'badge-primary' : 'badge-success'}`}>
                      {u.role.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {u.role === 'teacher' ? (
                      <input 
                        type="text" 
                        defaultValue={u.subject || ''} 
                        onBlur={(e) => {
                          if (e.target.value !== u.subject) handleAssignSubject(u.id, e.target.value);
                        }}
                        style={{ padding: '0.25rem 0.5rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', color: 'white', borderRadius: '4px' }}
                      />
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>N/A</span>
                    )}
                  </td>
                  <td>
                    {u.role !== 'admin' && (
                      <button onClick={() => handleDeleteUser(u.id)} className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem', color: 'var(--danger)', borderColor: 'var(--danger)' }}>
                        <Trash2 size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-card">
        <h2>Global Attendance Logs</h2>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Subject</th>
                <th>Student</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.logs.map((log, idx) => (
                <tr key={idx}>
                  <td>{log.date}</td>
                  <td><span className="badge badge-primary">{log.subject}</span></td>
                  <td style={{ fontWeight: '500' }}>{log.username}</td>
                  <td>
                    <span className={`badge ${log.status === 'Present' ? 'badge-success' : 'badge-danger'}`}>
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))}
              {data.logs.length === 0 && (
                <tr><td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No logs found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
