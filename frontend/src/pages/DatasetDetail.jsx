import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getDataset, getIncidents } from '../api/client'

export default function DatasetDetail() {
  const { id } = useParams()
  const [dataset, setDataset] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getDataset(id), getIncidents({ dataset_id: id })])
      .then(([ds, inc]) => {
        setDataset(ds.data)
        setIncidents(inc.data)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loading">Loading...</div>
  if (!dataset) return <div>Dataset not found</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/datasets" style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>← Datasets</Link>
          <h1 className="page-title" style={{ marginTop: '8px' }}>{dataset.name}</h1>
        </div>
        <span className={`badge badge-${dataset.status}`}>{dataset.status}</span>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{dataset.event_count}</div>
          <div className="stat-label">Events</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{dataset.incident_count}</div>
          <div className="stat-label">Incidents</div>
        </div>
      </div>

      {dataset.description && (
        <div className="card" style={{ marginBottom: '16px' }}>
          <p style={{ color: 'var(--text-secondary)' }}>{dataset.description}</p>
        </div>
      )}

      {dataset.parse_errors?.length > 0 && (
        <div className="card" style={{ marginBottom: '16px', borderColor: 'var(--danger)' }}>
          <h3 style={{ color: 'var(--danger)', marginBottom: '8px' }}>Parse Errors</h3>
          {dataset.parse_errors.map((e, i) => (
            <div key={i} style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              {e.file}: {e.error}
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h3 style={{ marginBottom: '12px' }}>Incidents ({incidents.length})</h3>
        <table className="table">
          <thead>
            <tr><th>Title</th><th>Severity</th><th>Status</th><th>Confidence</th></tr>
          </thead>
          <tbody>
            {incidents.length === 0 ? (
              <tr><td colSpan="4" style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>No incidents correlated</td></tr>
            ) : incidents.map((inc) => (
              <tr key={inc.id}>
                <td><Link to={`/incidents/${inc.id}`}>{inc.title}</Link></td>
                <td><span className={`badge badge-${inc.severity}`}>{inc.severity}</span></td>
                <td><span className={`badge badge-${inc.status}`}>{inc.status}</span></td>
                <td>{inc.confidence}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
