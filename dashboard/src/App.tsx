import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Toaster } from '@/components/ui/toaster'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import WorkerDashboard from '@/pages/WorkerDashboard'
import ContractDetail from '@/pages/ContractDetail'
import InvoiceList from '@/pages/InvoiceList'
import NewInvoice from '@/pages/NewInvoice'
import FreelancerProfilePage from '@/pages/FreelancerProfilePage'
import ClientSharePage from '@/pages/ClientSharePage'
import AdminPanel from '@/pages/AdminPanel'
import BlocklistPage from '@/pages/BlocklistPage'
import DashboardLayout from '@/components/DashboardLayout'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const role = useAuthStore((s) => s.role)
  if (role !== 'admin') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/share/:token" element={<ClientSharePage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<WorkerDashboard />} />
          <Route path="contracts/:id" element={<ContractDetail />} />
          <Route path="invoices" element={<InvoiceList />} />
          <Route path="invoices/new" element={<NewInvoice />} />
          <Route path="profile" element={<FreelancerProfilePage />} />
          <Route path="blocklist" element={<BlocklistPage />} />
          <Route
            path="admin"
            element={
              <AdminRoute>
                <AdminPanel />
              </AdminRoute>
            }
          />
        </Route>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}
