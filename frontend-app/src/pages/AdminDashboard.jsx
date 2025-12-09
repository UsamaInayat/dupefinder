import { useState } from 'react'
import '../styles/AdminDashboard.css'

// Import module components
import UserManagement from '../components/admin/UserManagement'
import ProductManagement from '../components/admin/ProductManagement'
import MLTraining from '../components/admin/MLTraining'
import ScrapingManagement from '../components/admin/ScrapingManagement'
import Overview from '../components/admin/Overview'

function AdminDashboard({ onLogout }) {
  const [activeModule, setActiveModule] = useState('overview')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const modules = [
    { id: 'overview', name: 'Overview', icon: '■' },
    { id: 'users', name: 'User Management', icon: '●' },
    { id: 'products', name: 'Product Catalogue', icon: '▪' },
    { id: 'training', name: 'ML Training', icon: '▸' },
    { id: 'scraping', name: 'Auto Sync', icon: '○' }
  ]

  const renderModule = () => {
    switch (activeModule) {
      case 'overview':
        return <Overview onNavigate={setActiveModule} />
      case 'users':
        return <UserManagement />
      case 'products':
        return <ProductManagement />
      case 'training':
        return <MLTraining />
      case 'scraping':
        return <ScrapingManagement />
      default:
        return <Overview onNavigate={setActiveModule} />
    }
  }

  return (
    <div className="admin-dashboard">
      {/* Fixed Header/Navbar */}
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

      {/* Sidebar */}
      <div className={`admin-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <nav className="admin-nav">
          {modules.map(module => (
            <button
              key={module.id}
              className={`nav-item ${activeModule === module.id ? 'active' : ''}`}
              onClick={() => setActiveModule(module.id)}
            >
              <span className="nav-text">{module.name}</span>
            </button>
          ))}
        </nav>

        <div className="admin-footer">
          <button onClick={onLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className={`admin-main ${sidebarCollapsed ? 'expanded' : ''}`}>
        <div className="admin-header">
          <div className="admin-user-info">
            <span>Admin Panel</span>
          </div>
        </div>

        <div className="admin-content" key={activeModule}>
          {renderModule()}
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard
