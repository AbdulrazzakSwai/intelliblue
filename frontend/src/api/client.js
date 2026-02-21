import axios from 'axios'

const API_BASE = '/api'

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client

// Auth
export const login = (username, password) => {
  const form = new FormData()
  form.append('username', username)
  form.append('password', password)
  return axios.post(`${API_BASE}/auth/login`, form)
}

// Datasets
export const getDatasets = () => client.get('/datasets/')
export const getDataset = (id) => client.get(`/datasets/${id}`)
export const deleteDataset = (id) => client.delete(`/datasets/${id}`)
export const uploadDataset = (formData) =>
  client.post('/datasets/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

// Events
export const getEvents = (params) => client.get('/events/', { params })

// Incidents
export const getIncidents = (params) => client.get('/incidents/', { params })
export const getIncident = (id) => client.get(`/incidents/${id}`)
export const acknowledgeIncident = (id) => client.post(`/incidents/${id}/acknowledge`)
export const updateIncident = (id, data) => client.patch(`/incidents/${id}`, data)
export const closeIncident = (id) => client.post(`/incidents/${id}/close`)
export const summarizeIncident = (id) => client.post(`/incidents/${id}/summarize`)
export const getIncidentEvents = (id) => client.get(`/incidents/${id}/events`)

// Notes
export const getNotes = (incidentId) => client.get(`/notes/incidents/${incidentId}/notes`)
export const addNote = (incidentId, data) => client.post(`/notes/incidents/${incidentId}/notes`, data)

// Chat
export const getChatSessions = () => client.get('/chat/sessions')
export const createChatSession = (data) => client.post('/chat/sessions', data)
export const getMessages = (sessionId) => client.get(`/chat/sessions/${sessionId}/messages`)
export const sendMessage = (sessionId, content) =>
  client.post(`/chat/sessions/${sessionId}/messages`, { content })

// Reports
export const downloadPdf = (incidentId) =>
  client.get(`/reports/incidents/${incidentId}/pdf`, { responseType: 'blob' })

// Users (Admin)
export const getUsers = () => client.get('/users/')
export const createUser = (data) => client.post('/users/', data)
export const updateUser = (id, data) => client.patch(`/users/${id}`, data)
export const getMe = () => client.get('/users/me')

// Audit Log (Admin)
export const getAuditLog = (params) => client.get('/admin/audit-log', { params })
