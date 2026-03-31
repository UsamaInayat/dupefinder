import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line
} from 'recharts'

function Overview({ onNavigate }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    setLoading(true)
    const token = localStorage.getItem('adminToken') || localStorage.getItem('token')

    if (!token) {
      console.log('No admin token found')
      setStats({
        users: 0,
        products: 0,
        communityPosts: 0,
        wishlistItems: 0,
        compareItems: 0,
        dupeHistoryClicks: 0,
        reviews: 0,
        pendingReports: 0,
        mostClicked: { name: 'N/A', clicks: 0, brand: null },
        graphBreakdown: [],
        graphDaily: { labels: [], community_posts: [], reports: [] }
      })
      setLoading(false)
      return
    }

    try {
      const response = await axios.get('http://localhost:8000/api/admin/overview-insights', {
        headers: { Authorization: `Bearer ${token}` }
      })
      const d = response.data || {}
      setStats({
        users: d.total_users || 0,
        products: d.total_products || 0,
        communityPosts: d.total_community_posts || 0,
        wishlistItems: d.total_wishlist_items || 0,
        compareItems: d.total_compare_items || 0,
        dupeHistoryClicks: d.total_dupe_history_clicks || 0,
        reviews: d.total_reviews || 0,
        pendingReports: d.pending_reports || 0,
        mostClicked: d.most_clicked_item || { name: 'N/A', clicks: 0, brand: null },
        graphBreakdown: d.graph_breakdown || [],
        graphDaily: d.graph_daily_activity || { labels: [], community_posts: [], reports: [] }
      })
    } catch (err) {
      console.log('Overview insights not ready yet:', err.message)
      setStats({
        users: 0,
        products: 0,
        communityPosts: 0,
        wishlistItems: 0,
        compareItems: 0,
        dupeHistoryClicks: 0,
        reviews: 0,
        pendingReports: 0,
        mostClicked: { name: 'N/A', clicks: 0, brand: null },
        graphBreakdown: [],
        graphDaily: { labels: [], community_posts: [], reports: [] }
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading statistics...</div>
  }

  const usageData = (stats?.graphBreakdown || []).map((x) => ({
    name: x.label,
    value: x.value
  }))

  const dailyData = (stats?.graphDaily?.labels || []).map((label, idx) => ({
    day: label,
    posts: stats?.graphDaily?.community_posts?.[idx] || 0,
    reports: stats?.graphDaily?.reports?.[idx] || 0
  }))

  return (
    <div className="overview-module">
      <div className="stats-grid">
        <div className="stat-card" onClick={() => onNavigate && onNavigate('users')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">●</div>
          <div className="stat-info">
            <h3>{stats?.users || 0}</h3>
            <p>Total Users</p>
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate && onNavigate('products')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">▪</div>
          <div className="stat-info">
            <h3>{stats?.products || 0}</h3>
            <p>Total Products</p>
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">▸</div>
          <div className="stat-info">
            <h3>{stats?.mostClicked?.clicks || 0}</h3>
            <p>Most Clicked Item</p>
            <small style={{ display: 'block', color: '#666', marginTop: 4 }}>
              {stats?.mostClicked?.name || 'N/A'}
            </small>
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate && onNavigate('moderation')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">○</div>
          <div className="stat-info">
            <h3>{stats?.communityPosts || 0}</h3>
            <p>Community Posts</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">◆</div>
          <div className="stat-info">
            <h3>{stats?.wishlistItems || 0}</h3>
            <p>Wishlist Items</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">◈</div>
          <div className="stat-info">
            <h3>{stats?.compareItems || 0}</h3>
            <p>Compare Items</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">◎</div>
          <div className="stat-info">
            <h3>{stats?.dupeHistoryClicks || 0}</h3>
            <p>Dupe History Clicks</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">★</div>
          <div className="stat-info">
            <h3>{stats?.reviews || 0}</h3>
            <p>Total Reviews</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('moderation')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">⚑</div>
          <div className="stat-info">
            <h3>{stats?.pendingReports || 0}</h3>
            <p>Pending Reports</p>
          </div>
        </div>
      </div>

      <div className="section-card" style={{ marginBottom: 20 }}>
        <h3>Usage Breakdown</h3>
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={usageData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.2)" />
              <XAxis dataKey="name" stroke="#fff" tick={{ fill: '#fff', fontSize: 12 }} />
              <YAxis stroke="#fff" tick={{ fill: '#fff', fontSize: 12 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: '#2f2a7d', border: '1px solid #ef4444', borderRadius: 8 }}
                labelStyle={{ color: '#fff' }}
              />
              <Legend wrapperStyle={{ color: '#fff' }} />
              <Bar dataKey="value" name="Count" fill="#ef4444" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="section-card">
        <h3>7-Day Community Activity</h3>
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={dailyData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.2)" />
              <XAxis dataKey="day" stroke="#fff" tick={{ fill: '#fff', fontSize: 12 }} />
              <YAxis stroke="#fff" tick={{ fill: '#fff', fontSize: 12 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: '#2f2a7d', border: '1px solid #ef4444', borderRadius: 8 }}
                labelStyle={{ color: '#fff' }}
              />
              <Legend wrapperStyle={{ color: '#fff' }} />
              <Line type="monotone" dataKey="posts" name="Posts" stroke="#8b85ff" strokeWidth={3} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="reports" name="Reports" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ marginTop: 14 }}>
        <button className="action-btn" onClick={() => onNavigate && onNavigate('moderation')}>
          Open Community Moderation
        </button>
      </div>
    </div>
  )
}

export default Overview

