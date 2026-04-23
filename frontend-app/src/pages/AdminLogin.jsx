import { useState } from 'react'
import axios from 'axios'
import { apiUrl } from '../lib/apiBase'
import '../styles/Auth.css'

function EmailFieldIcon() {
  return (
    <svg className="admin-login-field-icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden>
      <path
        fill="currentColor"
        d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"
      />
    </svg>
  )
}

function AdminLogin({ onLoginSuccess }) {
  const [email, setEmail] = useState('admin@dupefinder.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const adminLoginUrl = apiUrl('/api/admin/login')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await axios.post(
        adminLoginUrl,
        { email, password },
        { timeout: 25000 },
      )

      const { access_token, admin } = response.data

      localStorage.setItem('adminToken', access_token)
      localStorage.setItem('adminData', JSON.stringify(admin))

      onLoginSuccess(admin, access_token)
    } catch (err) {
      const msg =
        err.code === 'ECONNABORTED' || err.message?.toLowerCase?.().includes('timeout')
          ? 'Login timed out. Check API service health and VITE_API_BASE.'
          : err.response?.data?.detail || err.message || 'Login failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container admin-login admin-login--fullbg">
      <div
        className="admin-login-bg"
        style={{ backgroundImage: 'url(/login.png)' }}
        aria-hidden
      />
      <div className="admin-login-full-inner">
        <div className="auth-box admin-login-card">
          <div className="auth-header">
            <h2>Admin Login</h2>
            <p>DupeFinder Administration Panel</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            {error ? <div className="auth-error">{error}</div> : null}

            <div className="form-group">
              <label htmlFor="admin-login-email">Admin Email</label>
              <div className="admin-login-input-wrap">
                <span className="admin-login-input-icon-slot" aria-hidden>
                  <EmailFieldIcon />
                </span>
                <input
                  id="admin-login-email"
                  name="email"
                  type="email"
                  autoComplete="username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@dupefinder.com"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="admin-login-password">Admin Password</label>
              <div className="admin-login-input-wrap admin-login-input-wrap--password">
                <input
                  id="admin-login-password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button type="submit" className="auth-button admin-login-submit" disabled={loading}>
              {loading ? 'Logging in…' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default AdminLogin
