import { lazy, Suspense, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { adminApiUrl } from '../../lib/adminApiUrl'
import { adminKeys } from '../../adminQueryKeys'

const OverviewCharts = lazy(() => import('./OverviewCharts'))

const DEFAULT_STATS = {
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
  graphDaily: { labels: [], community_posts: [], reports: [] },
}

function mapInsightsPayload(d) {
  return {
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
    graphDaily: d.graph_daily_activity || { labels: [], community_posts: [], reports: [] },
  }
}

function Overview({ onNavigate }) {
  const { data: stats = DEFAULT_STATS } = useQuery({
    queryKey: adminKeys.overviewInsights,
    queryFn: async () => {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      if (!token) return { ...DEFAULT_STATS }
      const response = await axios.get(adminApiUrl('/overview-insights'), {
        headers: { Authorization: `Bearer ${token}` },
      })
      return mapInsightsPayload(response.data || {})
    },
    staleTime: 60_000,
    placeholderData: (previousData) => previousData,
  })

  useEffect(() => {
    import('./OverviewCharts').catch(() => {})
  }, [])

  const usageData = (stats.graphBreakdown || []).map((x) => ({
    name: x.label,
    value: x.value,
  }))

  const dailyData = (stats.graphDaily?.labels || []).map((label, idx) => ({
    day: label,
    posts: stats.graphDaily?.community_posts?.[idx] || 0,
    reports: stats.graphDaily?.reports?.[idx] || 0,
  }))

  return (
    <div className="overview-module">
      <div className="stats-grid">
        <div className="stat-card" onClick={() => onNavigate && onNavigate('users')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">●</div>
          <div className="stat-info">
            <h3>{stats.users}</h3>
            <p>Total Users</p>
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate && onNavigate('products')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">▪</div>
          <div className="stat-info">
            <h3>{stats.products}</h3>
            <p>Total Products</p>
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">▸</div>
          <div className="stat-info">
            <h3>{stats.mostClicked?.clicks || 0}</h3>
            <p>Most Clicked Item</p>
            <small style={{ display: 'block', color: 'var(--dupe-grey-subtitle)', marginTop: 4 }}>
              {stats.mostClicked?.name || 'N/A'}
            </small>
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate && onNavigate('moderation')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">○</div>
          <div className="stat-info">
            <h3>{stats.communityPosts}</h3>
            <p>Community Posts</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">◆</div>
          <div className="stat-info">
            <h3>{stats.wishlistItems}</h3>
            <p>Wishlist Items</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">◈</div>
          <div className="stat-info">
            <h3>{stats.compareItems}</h3>
            <p>Compare Items</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">◎</div>
          <div className="stat-info">
            <h3>{stats.dupeHistoryClicks}</h3>
            <p>Dupe History Clicks</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('overview')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">★</div>
          <div className="stat-info">
            <h3>{stats.reviews}</h3>
            <p>Total Reviews</p>
          </div>
        </div>
        <div className="stat-card" onClick={() => onNavigate && onNavigate('moderation')} style={{ cursor: 'pointer' }}>
          <div className="stat-icon">⚑</div>
          <div className="stat-info">
            <h3>{stats.pendingReports}</h3>
            <p>Pending Reports</p>
          </div>
        </div>
      </div>

      <Suspense
        fallback={
          <div className="section-card" style={{ marginBottom: 20 }}>
            <h3>Charts</h3>
            <div className="loading" style={{ padding: 24 }}>
              Loading charts…
            </div>
          </div>
        }
      >
        <OverviewCharts usageData={usageData} dailyData={dailyData} />
      </Suspense>

      <div style={{ marginTop: 14 }}>
        <button type="button" className="action-btn" onClick={() => onNavigate && onNavigate('moderation')}>
          Open Community Moderation
        </button>
      </div>
    </div>
  )
}

export default Overview
