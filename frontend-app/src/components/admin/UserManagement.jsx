import { useState, useEffect } from 'react'
import axios from 'axios'

function UserManagement() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    fetchUsers()
  }, [page, statusFilter])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20'
      })
      
      if (search) params.append('search', search)
      if (statusFilter !== 'all') params.append('status_filter', statusFilter)

      const response = await axios.get(
        `http://localhost:8000/api/admin/users?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setUsers(response.data.users)
      setTotalPages(response.data.total_pages)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch users:', error)
      setLoading(false)
    }
  }

  const handleDeactivate = async (userId) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return

    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      await axios.put(
        `http://localhost:8000/api/admin/users/${userId}/deactivate`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      alert('User deactivated successfully')
      fetchUsers()
    } catch (error) {
      console.error('Failed to deactivate user:', error)
      alert('Failed to deactivate user')
    }
  }

  const handleActivate = async (userId) => {
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      await axios.put(
        `http://localhost:8000/api/admin/users/${userId}/activate`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      alert('User activated successfully')
      fetchUsers()
    } catch (error) {
      console.error('Failed to activate user:', error)
      alert('Failed to activate user')
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    fetchUsers()
  }

  return (
    <div className="user-management">
      <div className="module-header">
        <h2>User Management</h2>
        <p>View and manage registered users</p>
      </div>

      <div className="filters-section">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search by email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="search-btn">Search</button>
        </form>

        <div className="filter-buttons">
          <button
            className={`filter-btn ${statusFilter === 'all' ? 'active' : ''}`}
            onClick={() => setStatusFilter('all')}
          >
            All
          </button>
          <button
            className={`filter-btn ${statusFilter === 'active' ? 'active' : ''}`}
            onClick={() => setStatusFilter('active')}
          >
            Active
          </button>
          <button
            className={`filter-btn ${statusFilter === 'inactive' ? 'active' : ''}`}
            onClick={() => setStatusFilter('inactive')}
          >
            Inactive
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading users...</div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Verified</th>
                  <th>Created</th>
                  <th>Last Login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user._id}>
                    <td>{user.email}</td>
                    <td>
                      <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${user.is_verified ? 'verified' : 'unverified'}`}>
                        {user.is_verified ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td>{new Date(user.created_at).toLocaleDateString()}</td>
                    <td>{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                    <td>
                      {user.is_active ? (
                        <button
                          onClick={() => handleDeactivate(user._id)}
                          className="action-btn danger"
                        >
                          Deactivate
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivate(user._id)}
                          className="action-btn success"
                        >
                          Activate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="pagination-btn"
            >
              Previous
            </button>
            <span className="pagination-info">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="pagination-btn"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default UserManagement




