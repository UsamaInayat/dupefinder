import { useState, useEffect } from 'react'
import axios from 'axios'
import '../styles/AdminPro.css'

function AdminDashboardPro({ admin, token, onLogout }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)

  const apiConfig = {
    headers: { Authorization: `Bearer ${token}` }
  }

  useEffect(() => {
    fetchStats()
    if (activeTab === 'users') fetchUsers()
    if (activeTab === 'products') fetchProducts()
  }, [activeTab])

  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/admin/stats', apiConfig)
      setStats(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      setLoading(false)
    }
  }

  const fetchUsers = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/admin/users', apiConfig)
      setUsers(response.data.users)
    } catch (error) {
      console.error('Failed to fetch users:', error)
    }
  }

  const fetchProducts = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/products')
      setProducts(response.data.products)
    } catch (error) {
      console.error('Failed to fetch products:', error)
    }
  }

  const toggleUserStatus = async (userId) => {
    try {
      await axios.put(`http://localhost:8000/api/admin/users/${userId}/status`, {}, apiConfig)
      fetchUsers()
      fetchStats()
    } catch (error) {
      console.error('Failed to toggle user status:', error)
      alert('Failed to update user status')
    }
  }

  const deleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      try {
        await axios.delete(`http://localhost:8000/api/admin/users/${userId}`, apiConfig)
        fetchUsers()
        fetchStats()
        alert('User deleted successfully')
      } catch (error) {
        console.error('Failed to delete user:', error)
        alert('Failed to delete user')
      }
    }
  }

  const deleteProduct = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        await axios.delete(`http://localhost:8000/api/admin/products/${productId}`, apiConfig)
        fetchProducts()
        fetchStats()
        alert('Product deleted successfully')
      } catch (error) {
        console.error('Failed to delete product:', error)
        alert('Failed to delete product')
      }
    }
  }

  return (
    <div className="admin-pro">
      {/* Header */}
      <header className="admin-pro-header">
        <div className="admin-pro-brand">
          <h1>DupeFinder</h1>
          <span className="admin-pro-subtitle">Administration Panel</span>
        </div>
        <div className="admin-pro-user">
          <div className="user-info">
            <span className="user-name">{admin?.full_name}</span>
            <span className="user-role">Administrator</span>
          </div>
          <button onClick={onLogout} className="btn-logout-pro">Logout</button>
        </div>
      </header>

      <div className="admin-pro-layout">
        {/* Sidebar */}
        <aside className="admin-pro-sidebar">
          <nav>
            <button
              className={activeTab === 'overview' ? 'active' : ''}
              onClick={() => setActiveTab('overview')}
            >
              <span className="nav-icon">▪</span>
              Dashboard Overview
            </button>
            <button
              className={activeTab === 'users' ? 'active' : ''}
              onClick={() => setActiveTab('users')}
            >
              <span className="nav-icon">▪</span>
              User Management
            </button>
            <button
              className={activeTab === 'products' ? 'active' : ''}
              onClick={() => setActiveTab('products')}
            >
              <span className="nav-icon">▪</span>
              Product Management
            </button>
            <button
              className={activeTab === 'analytics' ? 'active' : ''}
              onClick={() => setActiveTab('analytics')}
            >
              <span className="nav-icon">▪</span>
              Analytics & Reports
            </button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="admin-pro-content">
          {loading ? (
            <div className="loading-pro">
              <div className="spinner-pro"></div>
              <p>Loading data...</p>
            </div>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && stats && (
                <div className="content-section">
                  <div className="section-title">
                    <h2>Dashboard Overview</h2>
                    <p>System statistics and key metrics</p>
                  </div>
                  
                  <div className="stats-pro-grid">
                    <div className="stat-pro-card">
                      <div className="stat-pro-header">
                        <span className="stat-pro-label">Total Users</span>
                        <span className="stat-pro-badge">Active</span>
                      </div>
                      <div className="stat-pro-value">{stats.total_users}</div>
                      <div className="stat-pro-footer">
                        <span className="stat-trend">+ {stats.active_users_today} today</span>
                      </div>
                    </div>
                    
                    <div className="stat-pro-card">
                      <div className="stat-pro-header">
                        <span className="stat-pro-label">Total Products</span>
                        <span className="stat-pro-badge">Catalog</span>
                      </div>
                      <div className="stat-pro-value">{stats.total_products}</div>
                      <div className="stat-pro-footer">
                        <span className="stat-trend">5 categories</span>
                      </div>
                    </div>
                    
                    <div className="stat-pro-card">
                      <div className="stat-pro-header">
                        <span className="stat-pro-label">Total Searches</span>
                        <span className="stat-pro-badge">Activity</span>
                      </div>
                      <div className="stat-pro-value">{stats.total_searches}</div>
                      <div className="stat-pro-footer">
                        <span className="stat-trend">+ {stats.searches_today} today</span>
                      </div>
                    </div>
                    
                    <div className="stat-pro-card">
                      <div className="stat-pro-header">
                        <span className="stat-pro-label">Avg Response Time</span>
                        <span className="stat-pro-badge success">Healthy</span>
                      </div>
                      <div className="stat-pro-value">{stats.avg_search_time_ms.toFixed(1)}<span className="unit">ms</span></div>
                      <div className="stat-pro-footer">
                        <span className="stat-trend">Performance optimal</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid-2-col">
                    <div className="info-card">
                      <h3>Category Distribution</h3>
                      <div className="category-list-pro">
                        {stats.top_categories.map((cat) => (
                          <div key={cat._id} className="category-item-pro">
                            <div className="category-info">
                              <span className="category-name-pro">{cat._id.charAt(0).toUpperCase() + cat._id.slice(1)}</span>
                              <span className="category-count-pro">{cat.count} products</span>
                            </div>
                            <div className="category-bar-mini">
                              <div 
                                className="category-bar-fill"
                                style={{width: `${(cat.count / stats.total_products) * 100}%`}}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="info-card">
                      <h3>Recent User Registrations</h3>
                      <div className="user-list-pro-compact">
                        {stats.recent_users.slice(0, 5).map((user) => (
                          <div key={user._id} className="user-item-pro-compact">
                            <div className="user-avatar">{user.full_name.charAt(0)}</div>
                            <div className="user-details">
                              <span className="user-name-compact">{user.full_name}</span>
                              <span className="user-email-compact">{user.email}</span>
                            </div>
                            <span className="user-date">{new Date(user.created_at).toLocaleDateString()}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* User Management Tab */}
              {activeTab === 'users' && (
                <div className="content-section">
                  <div className="section-title">
                    <div>
                      <h2>User Management</h2>
                      <p>Manage registered users and permissions</p>
                    </div>
                    <div className="section-actions">
                      <span className="count-badge">{users.length} Total Users</span>
                    </div>
                  </div>

                  <div className="table-pro-container">
                    <table className="table-pro">
                      <thead>
                        <tr>
                          <th>User</th>
                          <th>Email</th>
                          <th>Status</th>
                          <th>Joined Date</th>
                          <th className="text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((user) => (
                          <tr key={user._id}>
                            <td>
                              <div className="user-cell">
                                <div className="user-avatar-small">{user.full_name.charAt(0)}</div>
                                <span className="user-name-cell">{user.full_name}</span>
                              </div>
                            </td>
                            <td>{user.email}</td>
                            <td>
                              <span className={`status-pro ${user.is_active ? 'active' : 'inactive'}`}>
                                {user.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td>{new Date(user.created_at).toLocaleDateString()}</td>
                            <td className="text-right">
                              <div className="action-buttons">
                                <button
                                  onClick={() => toggleUserStatus(user._id)}
                                  className="btn-action-pro"
                                  title={user.is_active ? 'Deactivate User' : 'Activate User'}
                                >
                                  {user.is_active ? 'Deactivate' : 'Activate'}
                                </button>
                                <button
                                  onClick={() => deleteUser(user._id)}
                                  className="btn-danger-pro"
                                  title="Delete User"
                                >
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Product Management Tab */}
              {activeTab === 'products' && (
                <div className="content-section">
                  <div className="section-title">
                    <div>
                      <h2>Product Management</h2>
                      <p>View and manage product catalog</p>
                    </div>
                    <div className="section-actions">
                      <span className="count-badge">{products.length} Products</span>
                    </div>
                  </div>

                  <div className="products-pro-grid">
                    {products.map((product) => (
                      <div key={product._id} className="product-pro-card">
                        <div className="product-pro-image">
                          <img
                            src={`http://localhost:8000/${product.image_path}`}
                            alt={product.name}
                            onError={(e) => {
                              e.target.src = 'https://via.placeholder.com/200?text=No+Image'
                            }}
                          />
                        </div>
                        <div className="product-pro-details">
                          <span className="product-pro-category">{product.category}</span>
                          <h4 className="product-pro-name">{product.name}</h4>
                          <p className="product-pro-brand">{product.brand}</p>
                          <div className="product-pro-footer">
                            <span className="product-pro-price">PKR {(parseFloat(product.price) * 280).toFixed(2)}</span>
                            <button
                              onClick={() => deleteProduct(product._id)}
                              className="btn-delete-pro"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Analytics Tab */}
              {activeTab === 'analytics' && stats && (
                <div className="content-section">
                  <div className="section-title">
                    <h2>Analytics & Reports</h2>
                    <p>System performance and usage analytics</p>
                  </div>
                  
                  <div className="analytics-pro-grid">
                    <div className="analytics-pro-card">
                      <h3>Today's Activity</h3>
                      <div className="analytics-pro-stats">
                        <div className="analytics-pro-stat">
                          <span className="analytics-pro-label">New Registrations</span>
                          <span className="analytics-pro-value">{stats.active_users_today}</span>
                        </div>
                        <div className="analytics-pro-stat">
                          <span className="analytics-pro-label">Searches Performed</span>
                          <span className="analytics-pro-value">{stats.searches_today}</span>
                        </div>
                      </div>
                    </div>

                    <div className="analytics-pro-card">
                      <h3>Performance Metrics</h3>
                      <div className="analytics-pro-stats">
                        <div className="analytics-pro-stat">
                          <span className="analytics-pro-label">Avg Search Time</span>
                          <span className="analytics-pro-value">{stats.avg_search_time_ms.toFixed(2)} ms</span>
                        </div>
                        <div className="analytics-pro-stat">
                          <span className="analytics-pro-label">System Status</span>
                          <span className="analytics-pro-value status-healthy">Healthy</span>
                        </div>
                      </div>
                    </div>

                    <div className="analytics-pro-card full-width-card">
                      <h3>Category Performance</h3>
                      <div className="category-performance">
                        {stats.top_categories.map((cat) => {
                          const percentage = (cat.count / stats.total_products) * 100
                          return (
                            <div key={cat._id} className="performance-bar-item">
                              <div className="performance-header">
                                <span className="performance-label">{cat._id.charAt(0).toUpperCase() + cat._id.slice(1)}</span>
                                <span className="performance-value">{cat.count} ({percentage.toFixed(1)}%)</span>
                              </div>
                              <div className="performance-bar-bg">
                                <div 
                                  className="performance-bar-progress"
                                  style={{width: `${percentage}%`}}
                                ></div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default AdminDashboardPro








