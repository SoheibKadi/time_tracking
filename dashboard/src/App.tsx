import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Toaster } from '@/components/ui/toaster'
import LoginPage from '@/pages/LoginPage'
import WorkerDashboard from '@/pages/WorkerDashboard'
import ContractDetail from '@/pages/ContractDetail'
import InvoiceList from '@/pages/InvoiceList'
import NewInvoice from '@/pages/NewInvoice'
import FreelancerProfilePage from '@/pages/FreelancerProfilePage'
import ClientSharePage from '@/pages/ClientSharePage'
import DashboardLayout from '@/components/DashboardLayout'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
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
        </Route>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}
