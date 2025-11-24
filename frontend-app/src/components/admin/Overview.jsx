import { useState, useEffect } from 'react'
import axios from 'axios'

function Overview({ onNavigate }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    // Set default stats immediately and stop loading
    setStats({
      users: 0,
      products: 0
    })
    setLoading(false)
    
    // Then try to fetch real data in background
    const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
    
    if (!token) {
      console.log('No admin token found')
      return
    }
    
    // Try to get user count
    try {
      const response = await axios.get('http://localhost:8000/api/admin/users?page=1&page_size=1', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.data && response.data.total !== undefined) {
        setStats(prev => ({ ...prev, users: response.data.total }))
      }
    } catch (err) {
      console.log('Users endpoint not ready yet')
    }
    
    // Try to get product count
    try {
      const productsResponse = await axios.get('http://localhost:8000/api/products?page=1&page_size=1')
      if (productsResponse.data && productsResponse.data.total !== undefined) {
        setStats(prev => ({ ...prev, products: productsResponse.data.total }))
      }
    } catch (err) {
      console.log('Products endpoint not ready yet:', err.message)
    }
  }

  if (loading) {
    return <div className="loading">Loading statistics...</div>
  }

  return (
    <div className="overview-module">
      <div className="welcome-section">
        <h2>Welcome to DupeFinder Admin Dashboard</h2>
        <p>Manage users, products, ML training, and data scraping</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">●</div>
          <div className="stat-info">
            <h3>{stats?.users || 0}</h3>
            <p>Total Users</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">▪</div>
          <div className="stat-info">
            <h3>{stats?.products || 0}</h3>
            <p>Total Products</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">▸</div>
          <div className="stat-info">
            <h3>Active</h3>
            <p>ML Model Status</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">○</div>
          <div className="stat-info">
            <h3>Ready</h3>
            <p>Sync Status</p>
          </div>
        </div>
      </div>

      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="action-buttons">
          <button 
            className="action-btn"
            onClick={() => onNavigate && onNavigate('users')}
          >
            Manage Users
          </button>
          <button 
            className="action-btn"
            onClick={() => onNavigate && onNavigate('products')}
          >
            Add Products
          </button>
          <button 
            className="action-btn"
            onClick={() => onNavigate && onNavigate('training')}
          >
            Train Model
          </button>
          <button 
            className="action-btn"
            onClick={() => onNavigate && onNavigate('scraping')}
          >
            Start Sync
          </button>
        </div>
      </div>
    </div>
  )
}

export default Overview

