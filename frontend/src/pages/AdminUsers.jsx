import { useState, useEffect } from 'react'
import { getUsers, createUser, updateUser } from '../api/client'

export default function AdminUsers() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', role: 'L1', full_name: '' })
  const [error, setError] = useState('')

  const load = () => getUsers().then((r) => setUsers(r.data)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await createUser(form)
      setShowForm(false)
      setForm({ username: '', password: '', role: 'L1', full_name: '' })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user')
    }
  }

  const toggleActive = async (user) => {
    await updateUser(user.id, { is_active: !user.is_active })
    load()
  }

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">User Management</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Cancel' : '+ New User'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card" style={{ marginBottom: '24px', maxWidth: '400px' }}>
          <h3 style={{ marginBottom: '12px' }}>Create User</h3>
          {['username', 'password', 'full_name'].map((field) => (
            <div key={field} className="form-group">
              <label>{field.replace('_', ' ')}</label>
              <input
                type={field === 'password' ? 'password' : 'text'}
                value={form[field]}
                onChange={(e) => setForm({ ...form, [field]: e.target.value })}
                required={field !== 'full_name'}
              />
            </div>
          ))}
          <div className="form-group">
            <label>Role</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="L1">L1 (Triage)</option>
              <option value="L2">L2 (Investigation)</option>
              <option value="ADMIN">Admin</option>
            </select>
          </div>
          {error && <div className="error-msg">{error}</div>}
          <button type="submit" className="btn-primary">Create User</button>
        </form>
      )}

      <div className="card">
        <table className="table">
          <thead>
            <tr><th>Username</th><th>Full Name</th><th>Role</th><th>Status</th><th>Last Login</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td style={{ fontFamily: 'monospace' }}>{u.username}</td>
                <td>{u.full_name || '—'}</td>
                <td><span className="badge" style={{ background: 'var(--bg-primary)' }}>{u.role}</span></td>
                <td>
                  <span style={{ color: u.is_active ? 'var(--success)' : 'var(--danger)' }}>
                    {u.is_active ? '● Active' : '○ Inactive'}
                  </span>
                </td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                </td>
                <td>
                  <button className="btn-ghost" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => toggleActive(u)}>
                    {u.is_active ? 'Disable' : 'Enable'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
