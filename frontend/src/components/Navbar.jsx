import React from 'react';
import { useAuth } from '../AuthContext';
import { GraduationCap, LogOut } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="logo">
        <GraduationCap className="w-8 h-8 text-primary" style={{ color: 'var(--primary)' }} />
        <span>Coders Hub University</span>
      </div>
      
      <div className="nav-links">
        {user && (
          <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginRight: '1rem' }}>
            {user.username} ({user.role})
          </span>
        )}
        <button onClick={logout} className="btn btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
