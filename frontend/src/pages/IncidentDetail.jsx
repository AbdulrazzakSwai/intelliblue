import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getIncident, acknowledgeIncident, closeIncident, updateIncident, summarizeIncident,
         getIncidentEvents, getNotes, addNote, downloadPdf } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export default function IncidentDetail() {
  const { id } = useParams()
  const { hasRole } = useAuth()
  const [incident, setIncident] = useState(null)
  const [events, setEvents] = useState([])
  const [notes, setNotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [noteContent, setNoteContent] = useState('')
  const [noteType, setNoteType] = useState('TRIAGE')
  const [summarizing, setSummarizing] = useState(false)
  const [summaryMsg, setSummaryMsg] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    const [inc, evs, nts] = await Promise.all([
      getIncident(id),
      getIncidentEvents(id),
      getNotes(id),
    ])
    setIncident(inc.data)
    setEvents(evs.data)
    setNotes(nts.data)
  }

  useEffect(() => {
    load().finally(() => setLoading(false))
  }, [id])

  const handleAck = async () => {
    await acknowledgeIncident(id)
    load()
  }

  const handleClose = async () => {
    if (!confirm('Close this incident?')) return
    await closeIncident(id)
    load()
  }

  const handleAddNote = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await addNote(id, { content: noteContent, note_type: noteType })
      setNoteContent('')
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add note')
    }
  }

  const handleSummarize = async () => {
    setSummarizing(true)
    setSummaryMsg('')
    try {
      const res = await summarizeIncident(id)
      setSummaryMsg(res.data.narrative || 'Summary generated. Reload to see.')
      load()
    } catch {
      setSummaryMsg('Summary generation failed or LLM not configured.')
    } finally {
      setSummarizing(false)
    }
  }

  const handleDownloadPdf = async () => {
    const res = await downloadPdf(id)
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `incident_${id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) return <div className="loading">Loading...</div>
  if (!incident) return <div>Incident not found</div>

  const latestSummary = incident.ai_summaries?.[incident.ai_summaries.length - 1]

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/incidents" style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>← Incidents</Link>
          <h1 className="page-title" style={{ marginTop: '8px', fontSize: '18px' }}>{incident.title}</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {incident.status === 'NEW' && (
            <button className="btn-ghost" onClick={handleAck}>Acknowledge</button>
          )}
          {hasRole('L2', 'ADMIN') && incident.status !== 'CLOSED' && (
            <button className="btn-ghost" onClick={handleClose}>Close</button>
          )}
          <button className="btn-ghost" onClick={handleSummarize} disabled={summarizing}>
            {summarizing ? 'Summarizing...' : '🤖 AI Summary'}
          </button>
          {hasRole('L2', 'ADMIN') && (
            <button className="btn-ghost" onClick={handleDownloadPdf}>📄 PDF</button>
          )}
        </div>
      </div>

      {summaryMsg && (
        <div className="card" style={{ marginBottom: '16px', borderColor: 'var(--accent)' }}>
          <p>{summaryMsg}</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div className="card">
          <h3 style={{ marginBottom: '12px' }}>Details</h3>
          <table className="table">
            <tbody>
              <tr><td style={{ color: 'var(--text-secondary)' }}>Severity</td><td><span className={`badge badge-${incident.severity}`}>{incident.severity}</span></td></tr>
              <tr><td style={{ color: 'var(--text-secondary)' }}>Status</td><td><span className={`badge badge-${incident.status}`}>{incident.status}</span></td></tr>
              <tr><td style={{ color: 'var(--text-secondary)' }}>Type</td><td>{incident.incident_type}</td></tr>
              <tr><td style={{ color: 'var(--text-secondary)' }}>Confidence</td><td>{incident.confidence}%</td></tr>
              <tr><td style={{ color: 'var(--text-secondary)' }}>Rule</td><td style={{ fontSize: '12px' }}>{incident.rule_id}</td></tr>
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '12px' }}>Rule Explanation</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            {incident.rule_explanation || 'No explanation available'}
          </p>
        </div>
      </div>

      {latestSummary && (
        <div className="card" style={{ marginBottom: '16px' }}>
          <h3 style={{ marginBottom: '12px' }}>🤖 AI Summary <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>({latestSummary.model_name || 'offline'})</span></h3>
          {latestSummary.narrative && <p style={{ marginBottom: '8px', lineHeight: '1.5' }}>{latestSummary.narrative}</p>}
          {latestSummary.summary_json && (
            <div style={{ fontSize: '13px' }}>
              {Object.entries(latestSummary.summary_json).map(([k, v]) => v && k !== 'summary' && (
                <div key={k} style={{ marginBottom: '6px' }}>
                  <strong style={{ color: 'var(--text-secondary)' }}>{k.replace(/_/g, ' ')}:</strong> {v}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="card" style={{ marginBottom: '16px' }}>
        <h3 style={{ marginBottom: '12px' }}>Evidence Timeline ({events.length} events)</h3>
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          <table className="table">
            <thead>
              <tr><th>Time</th><th>Source</th><th>Type</th><th>Src IP</th><th>User</th><th>Message</th></tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.id}>
                  <td style={{ fontSize: '12px', whiteSpace: 'nowrap' }}>{ev.event_time ? new Date(ev.event_time).toLocaleTimeString() : '-'}</td>
                  <td><span className="badge" style={{ background: 'var(--bg-primary)', fontSize: '10px' }}>{ev.source_type}</span></td>
                  <td style={{ fontSize: '12px' }}>{ev.event_type}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{ev.src_ip}</td>
                  <td style={{ fontSize: '12px' }}>{ev.username}</td>
                  <td style={{ fontSize: '12px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {ev.message || ev.signature || ev.url_path || ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '12px' }}>Analyst Notes</h3>
        {notes.map((note) => (
          <div key={note.id} style={{ marginBottom: '12px', padding: '10px', background: 'var(--bg-primary)', borderRadius: '6px', borderLeft: '3px solid var(--accent)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              [{note.note_type}] {new Date(note.created_at).toLocaleString()}
            </div>
            <p style={{ fontSize: '14px' }}>{note.content}</p>
          </div>
        ))}

        <form onSubmit={handleAddNote} style={{ marginTop: '16px' }}>
          {hasRole('L2', 'ADMIN') && (
            <div className="form-group">
              <label>Note Type</label>
              <select value={noteType} onChange={(e) => setNoteType(e.target.value)}>
                <option value="TRIAGE">TRIAGE</option>
                <option value="INVESTIGATION">INVESTIGATION</option>
              </select>
            </div>
          )}
          <div className="form-group">
            <label>Add Note</label>
            <textarea value={noteContent} onChange={(e) => setNoteContent(e.target.value)} placeholder="Enter note..." required />
          </div>
          {error && <div className="error-msg">{error}</div>}
          <button type="submit" className="btn-primary">Add Note</button>
        </form>
      </div>
    </div>
  )
}
