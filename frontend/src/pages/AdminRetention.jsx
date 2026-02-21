import { useState, useEffect } from 'react'
import { getDatasets, deleteDataset } from '../api/client'

export default function AdminRetention() {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => getDatasets().then((r) => setDatasets(r.data)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete dataset "${name}" and ALL its events, incidents, and notes? This is irreversible.`)) return
    await deleteDataset(id)
    load()
  }

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Data Retention</h1>
      </div>
      <div className="card">
        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px', fontSize: '14px' }}>
          Deleting a dataset permanently removes all associated events, incidents, notes, and AI summaries.
        </p>
        <table className="table">
          <thead>
            <tr><th>Dataset</th><th>Status</th><th>Events</th><th>Incidents</th><th>Uploaded</th><th>Action</th></tr>
          </thead>
          <tbody>
            {datasets.length === 0 ? (
              <tr><td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No datasets</td></tr>
            ) : datasets.map((ds) => (
              <tr key={ds.id}>
                <td>{ds.name}</td>
                <td><span className={`badge badge-${ds.status}`}>{ds.status}</span></td>
                <td>{ds.event_count}</td>
                <td>{ds.incident_count}</td>
                <td style={{ fontSize: '12px' }}>{new Date(ds.uploaded_at).toLocaleDateString()}</td>
                <td>
                  <button className="btn-danger" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => handleDelete(ds.id, ds.name)}>
                    Delete
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
