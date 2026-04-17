import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getInitials = (email: string) => {
    return email.substring(0, 2).toUpperCase();
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>✉ Remailder</h1>
          <p>Notification Service</p>
        </div>

        <nav className="sidebar-nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📊</span>
            Dashboard
          </NavLink>

          <NavLink
            to="/schedule"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📧</span>
            Programează Email
          </NavLink>

          <NavLink
            to="/history"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📋</span>
            Istoric
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user ? getInitials(user.email) : '?'}
            </div>
            <div className="user-details">
              <div className="name">{user?.email || 'Utilizator'}</div>
              <div className="role">Authenticated</div>
            </div>
          </div>
          <button
            className="nav-link"
            onClick={handleLogout}
            style={{ marginTop: '8px', color: '#ef4444' }}
          >
            <span className="nav-icon">🚪</span>
            Deconectare
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
