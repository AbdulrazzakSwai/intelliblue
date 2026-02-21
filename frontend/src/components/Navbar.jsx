import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const navItems = [
  { to: '/', label: '📊 Dashboard', roles: ['L1', 'L2', 'ADMIN'] },
  { to: '/datasets', label: '🗄️ Datasets', roles: ['L1', 'L2', 'ADMIN'] },
  { to: '/incidents', label: '🚨 Incidents', roles: ['L1', 'L2', 'ADMIN'] },
  { to: '/chat', label: '💬 Chat', roles: ['L1', 'L2', 'ADMIN'] },
  { to: '/admin/users', label: '👥 Users', roles: ['ADMIN'] },
  { to: '/admin/retention', label: '🗑️ Retention', roles: ['ADMIN'] },
  { to: '/admin/audit', label: '📋 Audit Log', roles: ['ADMIN'] },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav style={{
      width: '240px',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      top: 0, left: 0, bottom: 0,
      padding: '16px 0',
    }}>
      <div style={{ padding: '0 16px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--accent)' }}>
          🛡️ IntelliBlue
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          SOC Assistant
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {navItems
          .filter((item) => item.roles.includes(user?.role))
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              style={({ isActive }) => ({
                display: 'block',
                padding: '10px 16px',
                color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                background: isActive ? 'rgba(59,130,246,0.1)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                fontSize: '14px',
                transition: 'all 0.15s',
              })}
            >
              {item.label}
            </NavLink>
          ))}
      </div>

      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--border)',
        fontSize: '13px',
        color: 'var(--text-secondary)',
      }}>
        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{user?.full_name || user?.username}</div>
        <div style={{ fontSize: '11px', marginTop: '2px' }}>{user?.role}</div>
        <button
          onClick={handleLogout}
          style={{ marginTop: '8px', width: '100%', background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border)', padding: '6px', borderRadius: '4px', fontSize: '12px' }}
        >
          Sign Out
        </button>
      </div>
    </nav>
  )
}
