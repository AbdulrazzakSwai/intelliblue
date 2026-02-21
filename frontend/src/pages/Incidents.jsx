import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getIncidents } from '../api/client'

const STATUSES = ['', 'NEW', 'ACK', 'INVESTIGATING', 'CLOSED']
const SEVERITIES = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

export default function Incidents() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchParams, setSearchParams] = useSearchParams()

  const status = searchParams.get('status') || ''
  const severity = searchParams.get('severity') || ''

  useEffect(() => {
    const params = {}
    if (status) params.status = status
    if (severity) params.severity = severity
    params.limit = 100
    getIncidents(params)
      .then((r) => setIncidents(r.data))
      .finally(() => setLoading(false))
  }, [status, severity])

  const setFilter = (key, val) => {
    const p = new URLSearchParams(searchParams)
    if (val) p.set(key, val)
    else p.delete(key)
    setSearchParams(p)
  }

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Incidents ({incidents.length})</h1>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
        <select value={status} onChange={(e) => setFilter('status', e.target.value)}
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '6px 10px', borderRadius: '6px' }}>
          {STATUSES.map((s) => <option key={s} value={s}>{s || 'All Status'}</option>)}
        </select>
        <select value={severity} onChange={(e) => setFilter('severity', e.target.value)}
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '6px 10px', borderRadius: '6px' }}>
          {SEVERITIES.map((s) => <option key={s} value={s}>{s || 'All Severity'}</option>)}
        </select>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Type</th>
              <th>Confidence</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {incidents.length === 0 ? (
              <tr><td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No incidents found</td></tr>
            ) : incidents.map((inc) => (
              <tr key={inc.id}>
                <td><Link to={`/incidents/${inc.id}`}>{inc.title}</Link></td>
                <td><span className={`badge badge-${inc.severity}`}>{inc.severity}</span></td>
                <td><span className={`badge badge-${inc.status}`}>{inc.status}</span></td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{inc.incident_type}</td>
                <td>{inc.confidence}%</td>
                <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {new Date(inc.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
