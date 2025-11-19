import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import '../styles/Auth.css'

function Login({ onSwitchToSignup, onLoginSuccess, onSwitchToAdmin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await login(email, password)
    
    if (result.success) {
      onLoginSuccess()
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="auth-container">
      <div className="auth-box">
        <div className="auth-header">
          <h2>Welcome Back!</h2>
          <p>Login to DupeFinder</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
              minLength={6}
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

        <div className="auth-footer">
          <p>Don't have an account?</p>
          <button
            onClick={onSwitchToSignup}
            className="auth-link-button"
          >
            Sign up here
          </button>
          <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #eee' }}>
            <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: '5px' }}>Admin?</p>
            <button
              onClick={onSwitchToAdmin}
              className="auth-link-button"
              style={{ fontSize: '0.9rem' }}
            >
              Admin Login
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login

