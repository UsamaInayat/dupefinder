import { useState, useEffect } from 'react'
import AdminDashboard from './pages/AdminDashboard'
import AdminLogin from './pages/AdminLogin'

function MainApp() {
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
        localStorage.removeItem('adminToken')
        localStorage.removeItem('adminData')
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
        setView('adminDashboard')
      }}
    />
  )
}

function AppWithAuth() {
  return <MainApp />
}

export default AppWithAuth

