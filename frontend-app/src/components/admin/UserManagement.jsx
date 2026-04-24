import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import { adminApiUrl } from '../../lib/adminApiUrl'

function UserManagement() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [submittedSearch, setSubmittedSearch] = useState('')
  const hasLoadedOnce = useRef(false)

  const fetchUsers = useCallback(async () => {
    const silent = hasLoadedOnce.current
    if (!silent) setLoading(true)
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
      })

      if (submittedSearch) params.append('search', submittedSearch)

      const response = await axios.get(`${adminApiUrl('/users')}?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      setUsers(response.data.users)
      setTotalPages(response.data.total_pages)
    } catch (error) {
      console.error('Failed to fetch users:', error)
    } finally {
      hasLoadedOnce.current = true
      setLoading(false)
    }
  }, [page, submittedSearch])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const handleDelete = async (userId) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return

    const previous = users
    setUsers((u) => u.filter((x) => x._id !== userId))

    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      await axios.delete(adminApiUrl(`/users/${userId}`), {
        headers: { Authorization: `Bearer ${token}` },
      })
      alert('User deleted successfully')
    } catch (error) {
      console.error('Failed to delete user:', error)
      setUsers(previous)
      alert(error.response?.data?.detail || 'Failed to delete user')
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setSubmittedSearch(searchInput.trim())
    setPage(1)
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
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="search-btn">
            Search
          </button>
        </form>
      </div>

      {loading && users.length === 0 ? (
        <div className="loading">Loading users...</div>
      ) : (
        <>
          <div className="table-container" style={{ opacity: loading ? 0.65 : 1, transition: 'opacity 0.12s ease' }}>
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
                    <td
                      colSpan="5"
                      style={{ textAlign: 'center', padding: '40px', color: 'var(--dupe-grey-subtitle)' }}
                    >
                      No verified users found
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
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
                        <button type="button" onClick={() => handleDelete(user._id)} className="action-btn danger">
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div
            className="pagination"
            style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px', marginTop: '30px' }}
          >
            <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="pagination-btn">
              Previous
            </button>
            <span className="pagination-info">
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
