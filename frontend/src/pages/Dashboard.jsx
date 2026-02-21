import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getDatasets, getIncidents } from '../api/client'

export default function Dashboard() {
  const [datasets, setDatasets] = useState([])
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getDatasets(), getIncidents({ limit: 10 })])
      .then(([ds, inc]) => {
        setDatasets(ds.data)
        setIncidents(inc.data)
      })
      .finally(() => setLoading(false))
  }, [])

  const severityCounts = incidents.reduce((acc, i) => {
    acc[i.severity] = (acc[i.severity] || 0) + 1
    return acc
  }, {})

  if (loading) return <div className="loading">Loading dashboard...</div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{datasets.length}</div>
          <div className="stat-label">Datasets</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{incidents.length}</div>
          <div className="stat-label">Recent Incidents</div>
        </div>
        {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
          <div key={sev} className="stat-card">
            <div className="stat-value" style={{ color: `var(--${sev.toLowerCase()})` }}>
              {severityCounts[sev] || 0}
            </div>
            <div className="stat-label">{sev}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div className="card">
          <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>Recent Datasets</h3>
          {datasets.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>No datasets yet. <Link to="/datasets">Upload one →</Link></p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Incidents</th>
                </tr>
              </thead>
              <tbody>
                {datasets.slice(0, 5).map((ds) => (
                  <tr key={ds.id}>
                    <td><Link to={`/datasets/${ds.id}`}>{ds.name}</Link></td>
                    <td><span className={`badge badge-${ds.status}`}>{ds.status}</span></td>
                    <td>{ds.incident_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>Recent Incidents</h3>
          {incidents.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>No incidents yet.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {incidents.slice(0, 5).map((inc) => (
                  <tr key={inc.id}>
                    <td><Link to={`/incidents/${inc.id}`} style={{ fontSize: '13px' }}>{inc.title.substring(0, 40)}...</Link></td>
                    <td><span className={`badge badge-${inc.severity}`}>{inc.severity}</span></td>
                    <td><span className={`badge badge-${inc.status}`}>{inc.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
