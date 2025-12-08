import { useState, useEffect } from 'react'
import axios from 'axios'

function UserManagement() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetchUsers()
  }, [page])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20'
      })
      
      if (search) params.append('search', search)

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

  const handleDelete = async (userId) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return

    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      await axios.delete(
        `http://localhost:8000/api/admin/users/${userId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      alert('User deleted successfully')
      fetchUsers()
    } catch (error) {
      console.error('Failed to delete user:', error)
      alert(error.response?.data?.detail || 'Failed to delete user')
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
                  <th>Verified</th>
                  <th>Created</th>
                  <th>Last Login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: '#fff', opacity: 0.9 }}>
                      No verified users found
                    </td>
                  </tr>
                ) : (
                  users.map(user => (
                    <tr key={user._id}>
                      <td>{user.email}</td>
                      <td>
                        <span className={`status-badge ${user.is_verified ? 'verified' : 'unverified'}`}>
                          {user.is_verified ? 'Yes' : 'No'}
                        </span>
                      </td>
                      <td>{new Date(user.created_at).toLocaleDateString()}</td>
                      <td>{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                      <td>
                        <button
                          onClick={() => handleDelete(user._id)}
                          className="action-btn danger"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="pagination" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px', marginTop: '30px' }}>
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




