import { useState } from 'react'
import axios from 'axios'
import '../styles/Auth.css'

function AdminLogin({ onLoginSuccess }) {
  const [email, setEmail] = useState('admin@dupefinder.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await axios.post('http://localhost:8000/api/admin/login', {
        email,
        password
      })
      
      const { access_token, admin } = response.data
      
      localStorage.setItem('adminToken', access_token)
      localStorage.setItem('adminData', JSON.stringify(admin))
      
      onLoginSuccess(admin, access_token)
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-box">
        <div className="auth-header">
          <h2>Admin Login</h2>
          <p>DupeFinder Administration Panel</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label>Admin Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@dupefinder.com"
              required
            />
          </div>

          <div className="form-group">
            <label>Admin Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter admin password"
              required
            />
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default AdminLogin

