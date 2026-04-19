import { useState, useEffect } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './queryClient'
import AdminDashboard from './pages/AdminDashboard'
import AdminLogin from './pages/AdminLogin'

function MainAppInner() {
  // Check for admin token on mount to maintain state on refresh
  const [view, setView] = useState(() => {
    const adminToken = localStorage.getItem('adminToken')
    const adminData = localStorage.getItem('adminData')
    if (adminToken && adminData) {
      return 'adminDashboard'
    }
    return 'adminLogin'
  })

  useEffect(() => {
    // Check for admin token
    const adminToken = localStorage.getItem('adminToken')
    const adminData = localStorage.getItem('adminData')
    
    if (adminToken && adminData) {
      setView('adminDashboard')
    } else {
      setView('adminLogin')
    }
  }, [])

  // Admin Login View
  if (view === 'adminLogin') {
    return (
      <AdminLogin
        onLoginSuccess={(admin, token) => {
          // Store admin token
          localStorage.setItem('adminToken', token)
          localStorage.setItem('adminData', JSON.stringify(admin))
          // Always land on Overview after a new login (do not restore last session tab)
          localStorage.setItem('admin_active_module', 'overview')
          // Switch to admin dashboard view
          setView('adminDashboard')
        }}
      />
    )
  }

  // Admin Dashboard View
  if (view === 'adminDashboard') {
  const adminToken = localStorage.getItem('adminToken')
  const adminData = adminToken ? JSON.parse(localStorage.getItem('adminData') || '{}') : null
  
    if (adminToken && adminData) {
    return <AdminDashboard onLogout={() => {
      queryClient.clear()
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminData')
      localStorage.removeItem('admin_active_module')
      setView('adminLogin')
    }} />
  }
  }

  // Fallback to admin login
  return (
    <AdminLogin
      onLoginSuccess={(admin, token) => {
        localStorage.setItem('adminToken', token)
        localStorage.setItem('adminData', JSON.stringify(admin))
        localStorage.setItem('admin_active_module', 'overview')
        setView('adminDashboard')
      }}
    />
  )
}

function MainApp() {
  return (
    <QueryClientProvider client={queryClient}>
      <MainAppInner />
    </QueryClientProvider>
  )
}

function AppWithAuth() {
  return <MainApp />
}

export default AppWithAuth

