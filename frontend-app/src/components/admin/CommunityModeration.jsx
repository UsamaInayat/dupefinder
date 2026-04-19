import { useLayoutEffect, useRef, useState } from 'react'
import { FixedSizeList as List } from 'react-window'
import axios from 'axios'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { adminApiUrl } from '../../lib/adminApiUrl'
import { adminKeys } from '../../adminQueryKeys'

const POST_ROW_HEIGHT = 82
const POST_LIST_VIEWPORT = 440
const VIRTUAL_POSTS_THRESHOLD = 24

function authHeaders() {
  return {
    Authorization: `Bearer ${localStorage.getItem('adminToken') || localStorage.getItem('token')}`,
  }
}

async function fetchCommunityModeration() {
  const headers = authHeaders()
  const cfg = { headers, timeout: 45000 }
  const [rRes, pRes] = await Promise.all([
    axios.get(adminApiUrl('/community/reports?limit=80'), cfg),
    axios.get(adminApiUrl('/community/posts?limit=80'), cfg),
  ])
  return {
    reports: rRes.data?.reports || [],
    posts: pRes.data?.posts || [],
  }
}

function PostsVirtualList({ posts, onDeletePost, onBanUser }) {
  const wrapRef = useRef(null)
  const [width, setWidth] = useState(720)

  useLayoutEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(() => setWidth(Math.max(480, el.offsetWidth)))
    ro.observe(el)
    setWidth(Math.max(480, el.offsetWidth))
    return () => ro.disconnect()
  }, [])

  if (posts.length === 0) {
    return <p style={{ padding: 12, color: '#64748b' }}>No community posts.</p>
  }

  return (
    <div ref={wrapRef} style={{ width: '100%' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(64px,0.9fr) minmax(88px,1.4fr) 36px minmax(72px,0.7fr) 124px',
          gap: 6,
          padding: '8px 10px',
          fontSize: 12,
          fontWeight: 600,
          color: '#475569',
          borderBottom: '1px solid rgba(45,55,72,0.12)',
        }}
      >
        <div>Author</div>
        <div>Message</div>
        <div>Rpl</div>
        <div>Created</div>
        <div>Action</div>
      </div>
      <List height={POST_LIST_VIEWPORT} width={width} itemCount={posts.length} itemSize={POST_ROW_HEIGHT}>
        {({ index, style }) => {
          const p = posts[index]
          return (
            <div
              style={{
                ...style,
                boxSizing: 'border-box',
                display: 'grid',
                gridTemplateColumns: 'minmax(64px,0.9fr) minmax(88px,1.4fr) 36px minmax(72px,0.7fr) 124px',
                gap: 6,
                padding: '6px 10px',
                alignItems: 'center',
                background: index % 2 === 1 ? 'rgba(91,141,239,0.05)' : '#fff',
                borderBottom: '1px solid rgba(45,55,72,0.06)',
                fontSize: 13,
              }}
            >
              <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={p.author}>
                {p.author}
              </div>
              <div
                style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                title={p.description}
              >
                {p.description}
              </div>
              <div>{p.replies_count}</div>
              <div style={{ fontSize: 11, lineHeight: 1.2 }}>{new Date(p.created_at).toLocaleString()}</div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="action-btn danger"
                  style={{ fontSize: 11, padding: '4px 8px' }}
                  onClick={() => onDeletePost(p.id)}
                >
                  Delete
                </button>
                <button
                  type="button"
                  className="action-btn"
                  style={{ fontSize: 11, padding: '4px 8px' }}
                  onClick={() => onBanUser(p.author_user_id)}
                >
                  Ban
                </button>
              </div>
            </div>
          )
        }}
      </List>
    </div>
  )
}

function CommunityModeration() {
  const queryClient = useQueryClient()
  const { data, isPending, isFetching } = useQuery({
    queryKey: adminKeys.communityModeration,
    queryFn: fetchCommunityModeration,
    staleTime: 20_000,
    placeholderData: (previousData) => previousData,
  })

  const reports = data?.reports ?? []
  const posts = data?.posts ?? []
  const loading = isPending && !data
  const dimmed = isFetching && !!data

  const patchReports = (updater) => {
    queryClient.setQueryData(adminKeys.communityModeration, (old) => {
      const o = old || { reports: [], posts: [] }
      return { ...o, reports: typeof updater === 'function' ? updater(o.reports) : updater }
    })
  }

  const patchPosts = (updater) => {
    queryClient.setQueryData(adminKeys.communityModeration, (old) => {
      const o = old || { reports: [], posts: [] }
      return { ...o, posts: typeof updater === 'function' ? updater(o.posts) : updater }
    })
  }

  const handleResolve = async (reportId, action) => {
    const prev = queryClient.getQueryData(adminKeys.communityModeration)
    patchReports((r) => r.map((x) => (x.id === reportId ? { ...x, status: 'resolved' } : x)))
    try {
      await axios.put(
        adminApiUrl(`/community/reports/${reportId}/resolve?action=${action}`),
        {},
        { headers: authHeaders() },
      )
      await queryClient.invalidateQueries({ queryKey: adminKeys.communityModeration })
      await queryClient.invalidateQueries({ queryKey: adminKeys.overviewInsights })
    } catch (e) {
      if (prev) queryClient.setQueryData(adminKeys.communityModeration, prev)
      else await queryClient.invalidateQueries({ queryKey: adminKeys.communityModeration })
      alert('Failed to resolve report')
    }
  }

  const deletePost = async (postId) => {
    if (!window.confirm('Delete this post?')) return
    const prev = queryClient.getQueryData(adminKeys.communityModeration)
    patchPosts((p) => p.filter((x) => x.id !== postId))
    try {
      await axios.delete(adminApiUrl(`/community/posts/${postId}`), { headers: authHeaders() })
      await queryClient.invalidateQueries({ queryKey: adminKeys.communityModeration })
      await queryClient.invalidateQueries({ queryKey: adminKeys.overviewInsights })
    } catch (e) {
      if (prev) queryClient.setQueryData(adminKeys.communityModeration, prev)
      else await queryClient.invalidateQueries({ queryKey: adminKeys.communityModeration })
      alert('Failed to delete post')
    }
  }

  const banUser = async (userId) => {
    if (!userId) return alert('User id not found for this post.')
    if (!window.confirm('Ban this user and remove their posts?')) return
    const prev = queryClient.getQueryData(adminKeys.communityModeration)
    patchPosts((p) => p.filter((x) => x.author_user_id !== userId))
    try {
      await axios.put(adminApiUrl(`/community/users/${userId}/ban`), {}, { headers: authHeaders() })
      await queryClient.invalidateQueries({ queryKey: adminKeys.communityModeration })
      await queryClient.invalidateQueries({ queryKey: adminKeys.overviewInsights })
    } catch (e) {
      if (prev) queryClient.setQueryData(adminKeys.communityModeration, prev)
      else await queryClient.invalidateQueries({ queryKey: adminKeys.communityModeration })
      alert('Failed to ban user')
    }
  }

  return (
    <div className="content-section">
      <div className="section-title">
        <h2>Community Moderation</h2>
        <p>Review reports, delete harmful posts, and ban abusive users.</p>
      </div>

      {loading ? (
        <div className="section-card" style={{ padding: 24, textAlign: 'center', color: '#64748b' }}>
          Loading reports and posts…
        </div>
      ) : null}

      <div className="section-card" style={{ marginBottom: 20, opacity: loading || dimmed ? 0.55 : 1 }}>
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
                        <button type="button" className="action-btn" onClick={() => handleResolve(r.id, 'ignore')}>
                          Ignore
                        </button>
                        <button type="button" className="action-btn" onClick={() => handleResolve(r.id, 'delete_post')}>
                          Delete Post
                        </button>
                        <button type="button" className="action-btn danger" onClick={() => handleResolve(r.id, 'ban_user')}>
                          Ban User
                        </button>
                      </div>
                    ) : (
                      'Resolved'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="section-card" style={{ opacity: loading || dimmed ? 0.55 : 1 }}>
        <h3>All Community Posts</h3>
        {posts.length > VIRTUAL_POSTS_THRESHOLD ? (
          <PostsVirtualList posts={posts} onDeletePost={deletePost} onBanUser={banUser} />
        ) : (
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
                        <button type="button" className="action-btn danger" onClick={() => deletePost(p.id)}>
                          Delete
                        </button>
                        <button type="button" className="action-btn" onClick={() => banUser(p.author_user_id)}>
                          Ban User
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default CommunityModeration
