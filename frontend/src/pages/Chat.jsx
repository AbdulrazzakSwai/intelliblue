import { useState, useEffect, useRef } from 'react'
import { getChatSessions, createChatSession, getMessages, sendMessage } from '../api/client'
import { getDatasets, getIncidents } from '../api/client'

export default function Chat() {
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [datasets, setDatasets] = useState([])
  const [datasetId, setDatasetId] = useState('')
  const [incidentId, setIncidentId] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    getChatSessions().then((r) => setSessions(r.data))
    getDatasets().then((r) => setDatasets(r.data))
  }, [])

  useEffect(() => {
    if (activeSession) {
      getMessages(activeSession.id).then((r) => setMessages(r.data))
    }
  }, [activeSession])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleNewSession = async () => {
    const res = await createChatSession({
      title: `Chat ${new Date().toLocaleTimeString()}`,
      dataset_id: datasetId || null,
      incident_id: incidentId || null,
    })
    setSessions((s) => [res.data, ...s])
    setActiveSession(res.data)
    setMessages([])
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!activeSession || !input.trim()) return
    setSending(true)
    const userMsg = { id: Date.now(), role: 'USER', content: input, created_at: new Date().toISOString() }
    setMessages((m) => [...m, userMsg])
    setInput('')
    try {
      const res = await sendMessage(activeSession.id, input)
      setMessages((m) => [...m.filter((x) => x.id !== userMsg.id), { id: userMsg.id, role: 'USER', content: userMsg.content, created_at: userMsg.created_at }, res.data])
    } catch {
      setMessages((m) => [...m.filter((x) => x.id !== userMsg.id)])
    } finally {
      setSending(false)
    }
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 48px)', gap: '16px' }}>
      {/* Sessions sidebar */}
      <div style={{ width: '240px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div className="card" style={{ padding: '12px' }}>
          <div className="form-group" style={{ marginBottom: '8px' }}>
            <label>Dataset (optional)</label>
            <select value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
              <option value="">All</option>
              {datasets.map((ds) => <option key={ds.id} value={ds.id}>{ds.name}</option>)}
            </select>
          </div>
          <button className="btn-primary" style={{ width: '100%' }} onClick={handleNewSession}>
            + New Chat
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => setActiveSession(s)}
              style={{
                padding: '10px 12px',
                cursor: 'pointer',
                borderRadius: '6px',
                marginBottom: '4px',
                background: activeSession?.id === s.id ? 'var(--bg-card)' : 'transparent',
                border: '1px solid ' + (activeSession?.id === s.id ? 'var(--accent)' : 'transparent'),
                fontSize: '13px',
              }}
            >
              <div style={{ color: 'var(--text-primary)' }}>{s.title}</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>
                {new Date(s.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {!activeSession ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
            Select or create a chat session
          </div>
        ) : (
          <>
            <div className="card" style={{ flex: 1, overflowY: 'auto', marginBottom: '12px' }}>
              {messages.length === 0 && (
                <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '20px' }}>
                  Ask me anything about your incidents and logs.
                </div>
              )}
              {messages.map((msg) => (
                <div key={msg.id} style={{
                  marginBottom: '12px',
                  display: 'flex',
                  justifyContent: msg.role === 'USER' ? 'flex-end' : 'flex-start',
                }}>
                  <div style={{
                    maxWidth: '70%',
                    padding: '10px 14px',
                    borderRadius: '12px',
                    background: msg.role === 'USER' ? 'var(--accent)' : 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap',
                  }}>
                    {msg.content}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} style={{ display: 'flex', gap: '8px' }}>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about incidents, IPs, users..."
                style={{ flex: 1, padding: '10px 14px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-primary)' }}
              />
              <button type="submit" className="btn-primary" disabled={sending || !input.trim()}>
                {sending ? '...' : 'Send'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
