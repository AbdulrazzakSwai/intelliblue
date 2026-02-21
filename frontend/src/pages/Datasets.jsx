import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getDatasets, uploadDataset, deleteDataset } from '../api/client'
import { useAuth } from '../auth/AuthContext'

const FILE_TYPES = ['SIEM_JSON', 'WEB_LOG', 'SURICATA', 'SNORT']

export default function Datasets() {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [files, setFiles] = useState([])
  const [fileTypes, setFileTypes] = useState([])
  const [error, setError] = useState('')
  const { hasRole } = useAuth()

  const load = () => {
    getDatasets()
      .then((r) => setDatasets(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleFilesChange = (e) => {
    const selected = Array.from(e.target.files)
    setFiles(selected)
    setFileTypes(selected.map(() => 'SIEM_JSON'))
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    setError('')
    setUploading(true)
    try {
      const form = new FormData()
      form.append('name', name)
      if (description) form.append('description', description)
      files.forEach((f) => form.append('files', f))
      fileTypes.forEach((t) => form.append('file_types', t))
      await uploadDataset(form)
      setShowUpload(false)
      setName('')
      setDescription('')
      setFiles([])
      setFileTypes([])
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this dataset and all its events/incidents?')) return
    await deleteDataset(id)
    load()
  }

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Datasets</h1>
        {hasRole('ADMIN') && (
          <button className="btn-primary" onClick={() => setShowUpload(!showUpload)}>
            {showUpload ? '✕ Cancel' : '+ Upload Dataset'}
          </button>
        )}
      </div>

      {showUpload && (
        <form onSubmit={handleUpload} className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ marginBottom: '16px' }}>Upload New Dataset</h3>
          <div className="form-group">
            <label>Dataset Name *</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. January 2024 Logs" />
          </div>
          <div className="form-group">
            <label>Description</label>
            <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" />
          </div>
          <div className="form-group">
            <label>Log Files *</label>
            <input type="file" multiple onChange={handleFilesChange} required />
          </div>
          {files.map((f, i) => (
            <div key={i} className="form-group">
              <label>Type for {f.name}</label>
              <select value={fileTypes[i]} onChange={(e) => {
                const updated = [...fileTypes]
                updated[i] = e.target.value
                setFileTypes(updated)
              }}>
                {FILE_TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
          ))}
          {error && <div className="error-msg">{error}</div>}
          <button type="submit" className="btn-primary" disabled={uploading}>
            {uploading ? 'Uploading...' : 'Upload & Process'}
          </button>
        </form>
      )}

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Events</th>
              <th>Incidents</th>
              <th>Uploaded</th>
              {hasRole('ADMIN') && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {datasets.length === 0 ? (
              <tr><td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No datasets</td></tr>
            ) : datasets.map((ds) => (
              <tr key={ds.id}>
                <td><Link to={`/datasets/${ds.id}`}>{ds.name}</Link></td>
                <td><span className={`badge badge-${ds.status}`}>{ds.status}</span></td>
                <td>{ds.event_count}</td>
                <td>{ds.incident_count}</td>
                <td>{new Date(ds.uploaded_at).toLocaleDateString()}</td>
                {hasRole('ADMIN') && (
                  <td>
                    <button className="btn-danger" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => handleDelete(ds.id)}>
                      Delete
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
