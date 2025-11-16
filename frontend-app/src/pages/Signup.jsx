import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import '../styles/Auth.css'

function Signup({ onSwitchToLogin, onSignupSuccess }) {
  const [step, setStep] = useState(1) // 1: signup, 2: verify OTP
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const { signup, verifyOTP, resendOTP } = useAuth()

  const handleSignup = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    // Validate password match
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    const result = await signup(email, password)
    
    if (result.success) {
      setSuccess(result.message)
      setStep(2) // Move to OTP verification
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  const handleVerifyOTP = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    const result = await verifyOTP(email, otp)
    
    if (result.success) {
      setSuccess(result.message)
      setTimeout(() => {
        onSwitchToLogin() // Redirect to login after success
      }, 2000)
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  const handleResendOTP = async () => {
    setError('')
    setSuccess('')
    setLoading(true)

    const result = await resendOTP(email)
    
    if (result.success) {
      setSuccess('OTP resent successfully!')
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="auth-container">
      <div className="auth-box">
        <div className="auth-header">
          <h2>{step === 1 ? 'Join DupeFinder!' : 'Verify Your Email'}</h2>
          <p>{step === 1 ? 'Create your account' : 'Enter the OTP sent to your email'}</p>
        </div>

        {step === 1 ? (
          <form onSubmit={handleSignup} className="auth-form">
            {error && <div className="auth-error">{error}</div>}
            {success && <div className="auth-success">{success}</div>}

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
                placeholder="Min 8 characters with uppercase, lowercase, digit"
                required
                minLength={8}
                autoComplete="new-password"
              />
              <small>Must contain: uppercase, lowercase, and digit</small>
            </div>

            <div className="form-group">
              <label>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>

            <button type="submit" className="auth-button" disabled={loading}>
              {loading ? 'Creating account...' : 'Sign Up'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP} className="auth-form">
            {error && <div className="auth-error">{error}</div>}
            {success && <div className="auth-success">{success}</div>}

            <div className="form-group">
              <label>6-Digit OTP</label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="123456"
                required
                maxLength={6}
                style={{ fontSize: '1.5rem', textAlign: 'center', letterSpacing: '0.5rem' }}
              />
              <small>Check your email: {email}</small>
            </div>

            <button type="submit" className="auth-button" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify OTP'}
            </button>

            <button
              type="button"
              onClick={handleResendOTP}
              className="auth-link-button"
              disabled={loading}
              style={{ marginTop: '10px', width: '100%' }}
            >
              Resend OTP
            </button>
          </form>
        )}

        <div className="auth-footer">
          <p>Already have an account?</p>
          <button onClick={onSwitchToLogin} className="auth-link-button">
            Login here
          </button>
        </div>
      </div>
    </div>
  )
}

export default Signup

