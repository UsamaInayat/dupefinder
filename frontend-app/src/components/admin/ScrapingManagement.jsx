import { useState, useEffect } from 'react'
import axios from 'axios'

function ScrapingManagement() {
  const [brands, setBrands] = useState([])
  const [selectedBrands, setSelectedBrands] = useState([])
  const [scraping, setScraping] = useState(false)
  const [currentJob, setCurrentJob] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [history, setHistory] = useState([])
  const [brandType, setBrandType] = useState('local') // 'local', 'pakistani', or 'luxury'

  useEffect(() => {
    fetchBrands()
    fetchHistory()
  }, [brandType])

  useEffect(() => {
    if (currentJob && scraping) {
      const interval = setInterval(() => {
        checkScrapingStatus()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [currentJob, scraping])

  const fetchBrands = async () => {
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      
      if (!token) {
        alert('No admin token found. Please log out and log back in as admin.')
        return
      }
      
      console.log('Fetching brands with token:', token.substring(0, 20) + '...')
      
      const response = await axios.get(
        `http://localhost:8000/api/admin/scraping/brands?brand_type=${brandType}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setBrands(response.data.brands)
    } catch (error) {
      console.error('Failed to fetch brands:', error)
      const errorMsg = error.response?.data?.detail || error.message
      
      if (error.response?.status === 401) {
        alert('Authentication failed. Please log out and log back in as admin.\n\nError: ' + errorMsg)
        // Clear invalid token
        localStorage.removeItem('adminToken')
        localStorage.removeItem('adminData')
      } else {
        alert('Failed to load brands: ' + errorMsg)
      }
    }
  }

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      
      if (!token) {
        return // Don't show error for history, just skip
      }
      
      const response = await axios.get(
        'http://localhost:8000/api/admin/scraping/history?limit=5',
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setHistory(response.data.jobs)
    } catch (error) {
      console.error('Failed to fetch history:', error)
      // Don't show alert for history errors
    }
  }

  const toggleBrandSelection = (brand) => {
    setSelectedBrands(prev => {
      const exists = prev.some(b => b.brand_name === brand.brand_name && b.brand_url === brand.brand_url)
      if (exists) {
        return prev.filter(b => !(b.brand_name === brand.brand_name && b.brand_url === brand.brand_url))
      } else {
        return [...prev, brand]
      }
    })
  }

  const startScraping = async () => {
    if (selectedBrands.length === 0) {
      alert('Please select at least one brand')
      return
    }

    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const response = await axios.post(
        'http://localhost:8000/api/admin/scraping/start',
        { brand_ids: selectedBrands },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setCurrentJob(response.data.job_id)
      setScraping(true)
      setJobStatus(null)
    } catch (error) {
      console.error('Failed to start scraping:', error)
      alert('Failed to start scraping: ' + (error.response?.data?.detail || error.message))
    }
  }

  const checkScrapingStatus = async () => {
    if (!currentJob) return
    
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const response = await axios.get(
        `http://localhost:8000/api/admin/scraping/status/${currentJob}`,
        { 
          headers: { Authorization: `Bearer ${token}` },
          timeout: 5000  // 5 second timeout
        }
      )

      setJobStatus(response.data)

      if (response.data.status === 'completed') {
        setScraping(false)
        alert(`Scraping completed! ${response.data.products_added} products added`)
        fetchBrands()
        fetchHistory()
        setSelectedBrands([])
        setCurrentJob(null)
      } else if (response.data.status === 'failed') {
        setScraping(false)
        alert('Scraping failed: ' + (response.data.error || 'Unknown error'))
        setCurrentJob(null)
      }
    } catch (error) {
      // Don't spam console with network errors
      if (error.code !== 'ERR_NETWORK' && error.code !== 'ECONNABORTED') {
        console.error('Failed to check status:', error)
      }
      // If job doesn't exist or server is down, stop checking
      if (error.response?.status === 404) {
        setScraping(false)
        setCurrentJob(null)
      }
    }
  }

  return (
    <div className="scraping-management">
      <div className="module-header">
        <h2>Auto Sync / Rescraping</h2>
        <p>Select brands to rescrape and add new products</p>
      </div>

      {/* Brand Type Selector */}
      <div className="section-card">
        <h3>Brand Type</h3>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ marginRight: '15px' }}>
            <input
              type="radio"
              value="local"
              checked={brandType === 'local'}
              onChange={(e) => setBrandType(e.target.value)}
              disabled={scraping}
            />
            Local Affordable Brands
          </label>
          <label style={{ marginRight: '15px' }}>
            <input
              type="radio"
              value="pakistani"
              checked={brandType === 'pakistani'}
              onChange={(e) => setBrandType(e.target.value)}
              disabled={scraping}
            />
            Pakistani Designer Brands
          </label>
          <label>
            <input
              type="radio"
              value="luxury"
              checked={brandType === 'luxury'}
              onChange={(e) => setBrandType(e.target.value)}
              disabled={scraping}
            />
            Luxury/International Brands
          </label>
        </div>
      </div>

      {/* Brand Selection */}
      <div className="section-card">
        <h3>Select Brands to Rescrape ({brandType})</h3>
        {brands.length === 0 ? (
          <p style={{ color: '#999', padding: '20px' }}>
            No brands found for this type. Make sure Excel files are in the project root.
          </p>
        ) : (
          <>
            <div className="brand-grid">
          {brands.map((brand, idx) => {
            const isSelected = selectedBrands.some(
              b => b.brand_name === brand.brand_name && b.brand_url === brand.brand_url
            )
            return (
              <div
                key={`${brand.brand_name}-${brand.brand_url}-${idx}`}
                className={`brand-card ${isSelected ? 'selected' : ''}`}
                onClick={() => !scraping && toggleBrandSelection(brand)}
              >
                <div className="brand-checkbox">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}}
                    disabled={scraping}
                  />
                </div>
                <div className="brand-info">
                  <h4>{brand.brand_name}</h4>
                  <p>{brand.product_count || 0} products</p>
                  {brand.category && (
                    <small>Category: {brand.category}</small>
                  )}
                  {brand.last_scraped_at && (
                    <small>Last: {new Date(brand.last_scraped_at).toLocaleDateString()}</small>
                  )}
                </div>
              </div>
            )
          })}
            </div>

            <div className="selection-actions">
          <p>{selectedBrands.length} brand(s) selected</p>
          <button
            onClick={startScraping}
            disabled={scraping || selectedBrands.length === 0}
            className="scrape-btn"
          >
            {scraping ? 'Scraping in Progress...' : 'Start Scraping'}
          </button>
        </div>
          </>
        )}
      </div>

      {/* Progress Display */}
      {scraping && jobStatus && (
        <div className="section-card">
          <h3>Scraping Progress</h3>
          
          <div className="progress-info">
            <div className="progress-stats">
              <div className="stat">
                <span className="stat-label">Brands Completed</span>
                <span className="stat-value">
                  {jobStatus.brands_completed} / {jobStatus.brands_total}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Products Added</span>
                <span className="stat-value">{jobStatus.products_added}</span>
              </div>
            </div>

            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ 
                  width: `${(jobStatus.brands_completed / jobStatus.brands_total) * 100}%` 
                }}
              />
            </div>
          </div>

          {jobStatus.logs && jobStatus.logs.length > 0 && (
            <div className="logs-section">
              <h4>Activity Log:</h4>
              <div className="logs-container">
                {jobStatus.logs.map((log, idx) => (
                  <div key={idx} className="log-entry">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* History */}
      <div className="section-card">
        <h3>Scraping History</h3>
        
        {history.length === 0 ? (
          <p>No scraping history yet.</p>
        ) : (
          <div className="history-list">
            {history.map((job, idx) => (
              <div key={job.job_id || idx} className="history-item">
                <div className="history-header">
                  <span className="history-date">
                    {new Date(job.started_at).toLocaleString()}
                  </span>
                  <span className={`history-status ${job.status}`}>
                    {job.status}
                  </span>
                </div>
                <div className="history-details">
                  <span>Brands: {job.brands?.join(', ')}</span>
                  {job.products_added !== undefined && (
                    <span>Products Added: {job.products_added}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ScrapingManagement

