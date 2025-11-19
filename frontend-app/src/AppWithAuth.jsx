import { useState, useEffect } from 'react'
import App from './App'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import AdminDashboard from './pages/AdminDashboard'
import AdminLogin from './pages/AdminLogin'
import { AuthProvider, useAuth } from './context/AuthContext'

function MainApp() {
  const [view, setView] = useState('login') // Start at login page per requirements
  const { user, loading, logout } = useAuth()

  useEffect(() => {
    // If user is logged in, show admin dashboard
    if (user && user.is_verified) {
      setView('adminDashboard')
    } else if (!user) {
      setView('login')
    }
  }, [user])

  const handleLogout = () => {
    logout()
    setView('login')
  }

  // Views
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: '#fff',
        color: '#000',
        fontSize: '1.5rem'
      }}>
        Loading...
      </div>
    )
  }

  if (view === 'login') {
    return (
      <Login
        onSwitchToSignup={() => setView('signup')}
        onLoginSuccess={() => setView('adminDashboard')}
        onSwitchToAdmin={() => setView('adminLogin')}
      />
    )
  }

  if (view === 'signup') {
    return (
      <Signup
        onSwitchToLogin={() => setView('login')}
        onSignupSuccess={() => setView('login')}
      />
    )
  }

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

  // Check if admin is logged in
  const adminToken = localStorage.getItem('adminToken')
  const adminData = adminToken ? JSON.parse(localStorage.getItem('adminData') || '{}') : null
  
  if (adminToken && adminData && view === 'adminDashboard') {
    return <AdminDashboard onLogout={() => {
      localStorage.removeItem('adminToken')
      localStorage.removeItem('adminData')
      setView('login')
    }} />
  }

  if (view === 'adminDashboard' && user && user.is_verified) {
    return <AdminDashboard onLogout={handleLogout} />
  }

  // Fallback to login
  return (
    <Login
      onSwitchToSignup={() => setView('signup')}
      onLoginSuccess={() => setView('adminDashboard')}
      onSwitchToAdmin={() => setView('adminLogin')}
    />
  )
}

function AppWithAuth() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  )
}

export default AppWithAuth

