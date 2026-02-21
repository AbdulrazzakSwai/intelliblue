import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Datasets from './pages/Datasets'
import DatasetDetail from './pages/DatasetDetail'
import Incidents from './pages/Incidents'
import IncidentDetail from './pages/IncidentDetail'
import Chat from './pages/Chat'
import AdminUsers from './pages/AdminUsers'
import AdminRetention from './pages/AdminRetention'
import AuditLog from './pages/AuditLog'

function AppLayout({ children }) {
  return (
    <div className="layout">
      <Navbar />
      <main className="main-content">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={
          <ProtectedRoute>
            <AppLayout><Dashboard /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/datasets" element={
          <ProtectedRoute>
            <AppLayout><Datasets /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/datasets/:id" element={
          <ProtectedRoute>
            <AppLayout><DatasetDetail /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/incidents" element={
          <ProtectedRoute>
            <AppLayout><Incidents /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/incidents/:id" element={
          <ProtectedRoute>
            <AppLayout><IncidentDetail /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/chat" element={
          <ProtectedRoute>
            <AppLayout><Chat /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/users" element={
          <ProtectedRoute roles={['ADMIN']}>
            <AppLayout><AdminUsers /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/retention" element={
          <ProtectedRoute roles={['ADMIN']}>
            <AppLayout><AdminRetention /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="/admin/audit" element={
          <ProtectedRoute roles={['ADMIN']}>
            <AppLayout><AuditLog /></AppLayout>
          </ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
