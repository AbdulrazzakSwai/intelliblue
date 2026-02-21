import { useState, useEffect } from 'react'
import { getAuditLog } from '../api/client'

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  const load = (actionType = '') => {
    const params = { limit: 100 }
    if (actionType) params.action_type = actionType
    getAuditLog(params).then((r) => setLogs(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleFilter = (e) => {
    e.preventDefault()
    setLoading(true)
    load(filter)
  }

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Audit Log</h1>
      </div>

      <form onSubmit={handleFilter} style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter by action type (e.g., LOGIN_SUCCESS)"
          style={{ flex: 1, padding: '8px 12px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--text-primary)' }}
        />
        <button type="submit" className="btn-primary">Filter</button>
        <button type="button" className="btn-ghost" onClick={() => { setFilter(''); load() }}>Clear</button>
      </form>

      <div className="card">
        <table className="table">
          <thead>
            <tr><th>Time</th><th>Action</th><th>Target</th><th>User</th><th>Details</th><th>IP</th></tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr><td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No audit logs</td></tr>
            ) : logs.map((log) => (
              <tr key={log.id}>
                <td style={{ fontSize: '11px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                  {new Date(log.created_at).toLocaleString()}
                </td>
                <td><span className="badge" style={{ background: 'var(--bg-primary)', fontSize: '11px' }}>{log.action_type}</span></td>
                <td style={{ fontSize: '12px' }}>{log.target_type} {log.target_id?.substring(0, 8)}</td>
                <td style={{ fontSize: '12px', fontFamily: 'monospace' }}>{log.user_id?.substring(0, 8)}</td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{log.details}</td>
                <td style={{ fontSize: '12px', fontFamily: 'monospace' }}>{log.ip_addr || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
