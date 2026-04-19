import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react'
import '../styles/AdminDashboard.css'
import ScrapingManagement from '../components/admin/ScrapingManagement'
import CommunityModeration from '../components/admin/CommunityModeration'

const Overview = lazy(() => import('../components/admin/Overview'))
const UserManagement = lazy(() => import('../components/admin/UserManagement'))
const ProductManagement = lazy(() => import('../components/admin/ProductManagement'))

const moduleImporters = {
  overview: () => import('../components/admin/Overview'),
  users: () => import('../components/admin/UserManagement'),
  products: () => import('../components/admin/ProductManagement'),
}

function prefetchOverviewCharts() {
  import('../components/admin/OverviewCharts').catch(() => {})
}

function prefetchModule(moduleId) {
  const fn = moduleImporters[moduleId]
  if (fn) fn().catch(() => {})
}

function ModuleFallback({ label }) {
  return (
    <div className="section-card" style={{ padding: 28, textAlign: 'center', color: '#64748b' }}>
      <div className="loading" style={{ marginBottom: 8 }}>
        Loading {label}…
      </div>
      <p style={{ margin: 0, fontSize: 14 }}>Preparing this section (split bundle).</p>
    </div>
  )
}

const moduleLabels = {
  overview: 'Overview',
  users: 'User Management',
  products: 'Product Catalogue',
  scraping: 'Auto Sync',
  moderation: 'Community Moderation',
}

function panelStyle(isActive) {
  return {
    display: isActive ? 'block' : 'none',
    minHeight: isActive ? undefined : 0,
  }
}

function AdminDashboard({ onLogout }) {
  const initialModule = useMemo(
    () => (typeof localStorage !== 'undefined' ? localStorage.getItem('admin_active_module') || 'overview' : 'overview'),
    [],
  )

  const [activeModule, setActiveModule] = useState(initialModule)
  const [visitedModules, setVisitedModules] = useState(() => new Set([initialModule]))
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const openModule = useCallback((moduleId) => {
    prefetchModule(moduleId)
    setActiveModule(moduleId)
    setVisitedModules((prev) => new Set(prev).add(moduleId))
    localStorage.setItem('admin_active_module', moduleId)
  }, [])

  useEffect(() => {
    prefetchModule(activeModule)
    prefetchOverviewCharts()
    let idleId
    let t0
    if (typeof window.requestIdleCallback === 'function') {
      idleId = window.requestIdleCallback(() => prefetchOverviewCharts(), { timeout: 500 })
    } else {
      t0 = window.setTimeout(prefetchOverviewCharts, 0)
    }
    return () => {
      if (idleId != null) window.cancelIdleCallback?.(idleId)
      if (t0 != null) clearTimeout(t0)
    }
  }, [activeModule])

  useEffect(() => {
    const order = ['overview', 'users', 'products']
    const timers = order.map((id, i) => window.setTimeout(() => prefetchModule(id), 120 + i * 80))
    return () => timers.forEach(clearTimeout)
  }, [])

  const modules = [
    { id: 'overview', name: 'Overview', icon: '■' },
    { id: 'users', name: 'User Management', icon: '●' },
    { id: 'products', name: 'Product Catalogue', icon: '▪' },
    { id: 'scraping', name: 'Auto Sync', icon: '○' },
    { id: 'moderation', name: 'Community Moderation', icon: '◈' },
  ]

  const fallback = (id) => <ModuleFallback label={moduleLabels[id] || 'module'} />

  return (
    <div className="admin-dashboard">
      <div className="admin-navbar">
        <button
          className="hamburger-btn"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          aria-label="Toggle sidebar"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <h2 className="navbar-logo">DupeFinder Admin</h2>
        <div className="navbar-spacer"></div>
      </div>

      <div className={`admin-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <nav className="admin-nav">
          {modules.map((module) => (
            <button
              key={module.id}
              type="button"
              className={`nav-item ${activeModule === module.id ? 'active' : ''}`}
              onClick={() => openModule(module.id)}
              onFocus={() => prefetchModule(module.id)}
              onMouseEnter={() => prefetchModule(module.id)}
            >
              <span className="nav-text">{module.name}</span>
            </button>
          ))}
        </nav>

        <div className="admin-footer">
          <button type="button" onClick={onLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </div>

      <div className={`admin-main ${sidebarCollapsed ? 'expanded' : ''}`}>
        <div className="admin-content">
          {visitedModules.has('overview') ? (
            <div style={panelStyle(activeModule === 'overview')} aria-hidden={activeModule !== 'overview'}>
              <Suspense fallback={fallback('overview')}>
                <Overview onNavigate={openModule} />
              </Suspense>
            </div>
          ) : null}

          {visitedModules.has('users') ? (
            <div style={panelStyle(activeModule === 'users')} aria-hidden={activeModule !== 'users'}>
              <Suspense fallback={fallback('users')}>
                <UserManagement />
              </Suspense>
            </div>
          ) : null}

          {visitedModules.has('products') ? (
            <div style={panelStyle(activeModule === 'products')} aria-hidden={activeModule !== 'products'}>
              <Suspense fallback={fallback('products')}>
                <ProductManagement />
              </Suspense>
            </div>
          ) : null}

          {visitedModules.has('scraping') ? (
            <div style={panelStyle(activeModule === 'scraping')} aria-hidden={activeModule !== 'scraping'}>
              <ScrapingManagement />
            </div>
          ) : null}

          {visitedModules.has('moderation') ? (
            <div style={panelStyle(activeModule === 'moderation')} aria-hidden={activeModule !== 'moderation'}>
              <CommunityModeration />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard
