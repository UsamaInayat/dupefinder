import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import axios from 'axios'
import { getApiOrigin } from '../lib/apiOrigin'
import '../styles/Dashboard.css'

function Dashboard({ onBackToSearch }) {
  const { user, token, logout } = useAuth()
  const [searchHistory, setSearchHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetchSearchHistory()
    fetchSearchStats()
  }, [])

  const fetchSearchHistory = async () => {
    try {
      const response = await axios.get(`${getApiOrigin()}/api/auth/search-history?limit=10`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      setSearchHistory(response.data.searches || [])
    } catch (error) {
      console.error('Failed to fetch search history:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchSearchStats = async () => {
    try {
      const response = await axios.get(`${getApiOrigin()}/api/search/stats`)
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="dashboard-title">
          <h1>🏠 My Dashboard</h1>
          <p>Welcome back, {user?.full_name}!</p>
        </div>
        <div className="dashboard-actions">
          <button onClick={onBackToSearch} className="btn-primary">
            🔍 Back to Search
          </button>
          <button onClick={logout} className="btn-secondary">
            🚪 Logout
          </button>
        </div>
      </div>

      <div className="dashboard-container">
        {/* User Profile Card */}
        <div className="dashboard-card profile-card">
          <h2>👤 Profile</h2>
          <div className="profile-info">
            <div className="profile-item">
              <span className="label">Name:</span>
              <span className="value">{user?.full_name}</span>
            </div>
            <div className="profile-item">
              <span className="label">Email:</span>
              <span className="value">{user?.email}</span>
            </div>
            <div className="profile-item">
              <span className="label">Member Since:</span>
              <span className="value">{formatDate(user?.created_at)}</span>
            </div>
            <div className="profile-item">
              <span className="label">Status:</span>
              <span className="value">
                <span className="status-badge active">✅ Active</span>
              </span>
            </div>
          </div>
        </div>

        {/* Search Statistics */}
        {stats && (
          <div className="dashboard-card stats-card">
            <h2>📊 Search Statistics</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{stats.total_searches}</div>
                <div className="stat-label">Total Searches</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.avg_search_time_ms.toFixed(1)}ms</div>
                <div className="stat-label">Avg Search Time</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.min_search_time_ms.toFixed(1)}ms</div>
                <div className="stat-label">Fastest Search</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.max_search_time_ms.toFixed(1)}ms</div>
                <div className="stat-label">Slowest Search</div>
              </div>
            </div>
          </div>
        )}

        {/* Search History */}
        <div className="dashboard-card history-card">
          <h2>📜 Recent Search History</h2>
          
          {loading ? (
            <div className="loading-state">Loading...</div>
          ) : searchHistory.length === 0 ? (
            <div className="empty-state">
              <p>🔍 No search history yet</p>
              <p>Start searching to see your history here!</p>
              <button onClick={onBackToSearch} className="btn-primary">
                Start Searching
              </button>
            </div>
          ) : (
            <div className="history-list">
              {searchHistory.map((search, index) => (
                <div key={search._id || index} className="history-item">
                  <div className="history-header">
                    <span className="history-date">
                      🕐 {formatDate(search.timestamp)}
                    </span>
                    <span className="history-time">
                      ⚡ {search.search_time_ms?.toFixed(2)}ms
                    </span>
                  </div>
                  <div className="history-results">
                    <span className="results-count">
                      Found {search.results?.length || 0} similar products
                    </span>
                    {search.results && search.results.length > 0 && (
                      <div className="top-match">
                        Best Match: {(search.results[0].similarity_score * 100).toFixed(1)}% similarity
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard








