import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import './Navbar.css';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const cycleTheme = () => {
    const themes: Array<'light' | 'dark' | 'auto'> = ['light', 'dark', 'auto'];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  const getThemeIcon = () => {
    switch (theme) {
      case 'light':
        return '☀️';
      case 'dark':
        return '🌙';
      case 'auto':
        return '🔄';
    }
  };

  const isAdmin = user?.role === 'global_admin' || user?.role === 'ou_admin';

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">WaddlePerf Manager</Link>
      </div>
      <div className="navbar-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/devices">Devices</Link>
        <Link to="/statistics">Statistics</Link>
        {isAdmin && <Link to="/users">Users</Link>}
        {isAdmin && <Link to="/organizations">Organizations</Link>}
        <Link to="/profile">Profile</Link>
      </div>
      <div className="navbar-actions">
        <button className="theme-toggle" onClick={cycleTheme} title={`Theme: ${theme}`}>
          {getThemeIcon()}
        </button>
        <span className="user-info">{user?.username}</span>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
