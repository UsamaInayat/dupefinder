import { createContext, useState, useContext, useEffect, useRef } from 'react'
import axios from 'axios'
import { getApiBase } from '../lib/apiBase'

const AuthContext = createContext(null)

// Same-origin in dev (Vite proxies /api). In prod, VITE_API_BASE must point at the API.
const api = axios.create({
  baseURL: getApiBase() || undefined,
})

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)
  const refreshTimerRef = useRef(null)

  // Check if user data is stored on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser))
      } catch (error) {
        console.error('Failed to parse stored user:', error)
        logout()
      }
    }
    setLoading(false)
  }, [])

  // Setup axios interceptor for automatic token refresh
  useEffect(() => {
    // Request interceptor - add token to headers
    const requestInterceptor = api.interceptors.request.use(
      (config) => {
        const currentToken = localStorage.getItem('token')
        if (currentToken) {
          config.headers.Authorization = `Bearer ${currentToken}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor - handle token expiration
    const responseInterceptor = api.interceptors.response.use(
      (response) => {
        return response
      },
      async (error) => {
        const originalRequest = error.config

        // If token expired and we haven't tried to refresh yet
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = localStorage.getItem('refresh_token')
            if (!refreshToken) {
              logout()
              return Promise.reject(error)
            }

            // Try to refresh the token
            const response = await api.post('/api/auth/refresh', {
              refresh_token: refreshToken
            })

            const { access_token } = response.data
            localStorage.setItem('token', access_token)
            setToken(access_token)

            // Retry the original request with new token
            originalRequest.headers.Authorization = `Bearer ${access_token}`
            return api(originalRequest)
          } catch (refreshError) {
            // Refresh failed, logout user
            logout()
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )

    // Cleanup interceptors on unmount
    return () => {
      api.interceptors.request.eject(requestInterceptor)
      api.interceptors.response.eject(responseInterceptor)
    }
  }, [])

  // Automatic token refresh before expiry (every 25 days for 30-day token)
  useEffect(() => {
    if (token) {
      // Clear existing timer
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current)
      }

      // Set up automatic refresh (refresh 5 days before expiry)
      refreshTimerRef.current = setTimeout(async () => {
        await refreshToken()
      }, 25 * 24 * 60 * 60 * 1000) // 25 days in milliseconds
    }

    return () => {
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current)
      }
    }
  }, [token])

  const login = async (email, password) => {
    try {
      const response = await api.post('/api/auth/login', {
        email,
        password
      })
      
      const { access_token, refresh_token, user } = response.data
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('user', JSON.stringify(user))
      setToken(access_token)
      setUser(user)
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      }
    }
  }

  const signup = async (email, password) => {
    try {
      const response = await api.post('/api/auth/signup', {
        email,
        password
      })
      
      return { 
        success: true,
        message: response.data.message,
        email: response.data.email
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Signup failed'
      }
    }
  }

  const verifyOTP = async (email, otp_code) => {
    try {
      const response = await api.post('/api/auth/verify-otp', {
        email,
        otp_code
      })
      
      return { 
        success: true,
        message: response.data.message
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'OTP verification failed'
      }
    }
  }

  const resendOTP = async (email) => {
    try {
      const response = await api.post(`/api/auth/resend-otp?email=${encodeURIComponent(email)}`)
      
      return { 
        success: true,
        message: response.data.message
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to resend OTP'
      }
    }
  }

  const refreshToken = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token')
      if (!refresh_token) {
        throw new Error('No refresh token available')
      }

      const response = await api.post('/api/auth/refresh', {
        refresh_token: refresh_token
      })

      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      setToken(access_token)
      
      return { success: true }
    } catch (error) {
      console.error('Token refresh failed:', error)
      // Don't logout on refresh failure, let the interceptor handle it
      return { success: false }
    }
  }

  const logout = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token')
      if (refresh_token) {
        // Call logout endpoint to invalidate refresh token
        await api.post('/api/auth/logout', {
          refresh_token: refresh_token
        }).catch(() => {
          // Ignore errors on logout
        })
      }
    } catch (error) {
      // Ignore errors
    } finally {
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      setToken(null)
      setUser(null)
      
      // Clear refresh timer
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current)
      }
    }
  }

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      signup,
      verifyOTP,
      resendOTP,
      refreshToken,
      logout,
      isAuthenticated: !!user,
      api // Export axios instance with interceptors
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}



