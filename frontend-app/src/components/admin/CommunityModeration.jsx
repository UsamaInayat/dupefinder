import { useEffect, useState } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

function CommunityModeration() {
  const [reports, setReports] = useState([])
  const [posts, setPosts] = useState([])
  const token = localStorage.getItem('adminToken') || localStorage.getItem('token')

  const apiConfig = { headers: { Authorization: `Bearer ${token}` } }

  const load = async () => {
    try {
      const [rRes, pRes] = await Promise.all([
        axios.get(`${API_BASE}/api/admin/community/reports`, apiConfig),
        axios.get(`${API_BASE}/api/admin/community/posts`, apiConfig)
      ])
      setReports(rRes.data?.reports || [])
      setPosts(pRes.data?.posts || [])
    } catch (e) {
      console.error('Community moderation load failed', e)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleResolve = async (reportId, action) => {
    try {
      await axios.put(`${API_BASE}/api/admin/community/reports/${reportId}/resolve?action=${action}`, {}, apiConfig)
      await load()
    } catch (e) {
      alert('Failed to resolve report')
    }
  }

  const deletePost = async (postId) => {
    if (!window.confirm('Delete this post?')) return
    try {
      await axios.delete(`${API_BASE}/api/admin/community/posts/${postId}`, apiConfig)
      await load()
    } catch (e) {
      alert('Failed to delete post')
    }
  }

  const banUser = async (userId) => {
    if (!userId) return alert('User id not found for this post.')
    if (!window.confirm('Ban this user and remove their posts?')) return
    try {
      await axios.put(`${API_BASE}/api/admin/community/users/${userId}/ban`, {}, apiConfig)
      await load()
    } catch (e) {
      alert('Failed to ban user')
    }
  }

  return (
    <div className="content-section">
      <div className="section-title">
        <h2>Community Moderation</h2>
        <p>Review reports, delete harmful posts, and ban abusive users.</p>
      </div>

      <div className="section-card" style={{ marginBottom: 20 }}>
        <h3>Reported Posts</h3>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Reporter</th>
                <th>Reason</th>
                <th>Post</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.id}>
                  <td>{r.reporter_name || r.reporter_email || 'Unknown'}</td>
                  <td>{r.reason}</td>
                  <td>{r.post_excerpt}</td>
                  <td>{r.status}</td>
                  <td>
                    {r.status === 'pending' ? (
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button className="action-btn" onClick={() => handleResolve(r.id, 'ignore')}>Ignore</button>
                        <button className="action-btn" onClick={() => handleResolve(r.id, 'delete_post')}>Delete Post</button>
                        <button className="action-btn danger" onClick={() => handleResolve(r.id, 'ban_user')}>Ban User</button>
                      </div>
                    ) : 'Resolved'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="section-card">
        <h3>All Community Posts</h3>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Author</th>
                <th>Message</th>
                <th>Replies</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {posts.map((p) => (
                <tr key={p.id}>
                  <td>{p.author}</td>
                  <td>{p.description}</td>
                  <td>{p.replies_count}</td>
                  <td>{new Date(p.created_at).toLocaleString()}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button className="action-btn danger" onClick={() => deletePost(p.id)}>Delete</button>
                      <button className="action-btn" onClick={() => banUser(p.author_user_id)}>Ban User</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default CommunityModeration
