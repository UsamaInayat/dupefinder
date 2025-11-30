import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'

function ScrapingManagement() {
  const [brands, setBrands] = useState([])
  const [selectedBrands, setSelectedBrands] = useState([])
  const [scraping, setScraping] = useState(false)
  const [currentJob, setCurrentJob] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [history, setHistory] = useState([])
  const [historyPage, setHistoryPage] = useState(1)
  const [historyTotalPages, setHistoryTotalPages] = useState(1)
  const [historyTotal, setHistoryTotal] = useState(0)
  const [deletingHistoryId, setDeletingHistoryId] = useState(null)
  const [brandType, setBrandType] = useState('local') // Only 'local' is supported
  const [loadingBrands, setLoadingBrands] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  
  // Prevent multiple clicks
  const isProcessingRef = useRef(false)
  const lastClickTimeRef = useRef(0)

  const showNotification = (message, type) => {
    const notification = document.createElement('div')
    notification.className = `notification notification-${type}`
    notification.textContent = message
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      background: ${type === 'success' ? '#10b981' : '#ef4444'};
      color: #fff;
      border: 2px solid ${type === 'success' ? '#059669' : '#dc2626'};
      border-radius: 6px;
      z-index: 10000;
      font-size: 14px;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
      animation: none;
      transform: translateX(0);
      opacity: 1;
    `
    document.body.appendChild(notification)
    setTimeout(() => {
      notification.style.opacity = '0'
      notification.style.transition = 'opacity 0.2s'
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification)
        }
      }, 200)
    }, 3000)
  }

  const showConfirmDialog = (message, onConfirm, onCancel = null) => {
    const overlay = document.createElement('div')
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      z-index: 10001;
      display: flex;
      align-items: center;
      justify-content: center;
    `
    const dialog = document.createElement('div')
    dialog.style.cssText = `
      background: #fff;
      border-radius: 8px;
      padding: 24px;
      max-width: 400px;
      width: 90%;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
      z-index: 10002;
    `
    const messageEl = document.createElement('div')
    messageEl.textContent = message
    messageEl.style.cssText = `
      margin-bottom: 20px;
      font-size: 16px;
      color: #333;
      line-height: 1.5;
    `
    const buttonsContainer = document.createElement('div')
    buttonsContainer.style.cssText = `
      display: flex;
      gap: 10px;
      justify-content: flex-end;
    `
    const cancelBtn = document.createElement('button')
    cancelBtn.textContent = 'Cancel'
    cancelBtn.style.cssText = `
      padding: 10px 20px;
      background: #f3f4f6;
      color: #333;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
    `
    cancelBtn.onmouseover = () => cancelBtn.style.background = '#e5e7eb'
    cancelBtn.onmouseout = () => cancelBtn.style.background = '#f3f4f6'
    const confirmBtn = document.createElement('button')
    confirmBtn.textContent = 'Confirm'
    confirmBtn.style.cssText = `
      padding: 10px 20px;
      background: #ef4444;
      color: #fff;
      border: 1px solid #dc2626;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
    `
    confirmBtn.onmouseover = () => confirmBtn.style.background = '#dc2626'
    confirmBtn.onmouseout = () => confirmBtn.style.background = '#ef4444'
    const close = () => {
      document.body.removeChild(overlay)
    }
    cancelBtn.onclick = () => {
      close()
      if (onCancel) onCancel()
    }
    confirmBtn.onclick = () => {
      close()
      if (onConfirm) onConfirm()
    }
    buttonsContainer.appendChild(cancelBtn)
    buttonsContainer.appendChild(confirmBtn)
    dialog.appendChild(messageEl)
    dialog.appendChild(buttonsContainer)
    overlay.appendChild(dialog)
    document.body.appendChild(overlay)
    overlay.onclick = (e) => {
      if (e.target === overlay) {
        close()
        if (onCancel) onCancel()
      }
    }
  }

  // Define functions first (before useEffects that use them)
  const fetchBrands = async () => {
    setLoadingBrands(true)
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      
      if (!token) {
        showNotification('No admin token found. Please log out and log back in as admin.', 'error')
        setLoadingBrands(false)
        return
      }
      
      const response = await axios.get(
        `http://localhost:8000/api/admin/scraping/brands?brand_type=${brandType}`,
        { 
          headers: { Authorization: `Bearer ${token}` }
          // Removed timeout to allow backend to take as long as needed
        }
      )
      setBrands(response.data.brands || [])
    } catch (error) {
      console.error('Failed to fetch brands:', error)
      const errorMsg = error.response?.data?.detail || error.message
      
      if (error.response?.status === 401) {
        showNotification('Authentication failed. Please log out and log back in as admin. Error: ' + errorMsg, 'error')
        // Clear invalid token
        localStorage.removeItem('adminToken')
        localStorage.removeItem('adminData')
      } else if (error.code === 'ECONNABORTED') {
        // Timeout error - don't show alert, just log
        console.error('Request timeout - backend is taking too long')
      } else {
        // Only show alert for non-timeout errors
        if (!error.code || error.code !== 'ECONNABORTED') {
          showNotification('Failed to load brands: ' + errorMsg, 'error')
        }
      }
    } finally {
      setLoadingBrands(false)
    }
  }

  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true)
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      
      if (!token) {
        setLoadingHistory(false)
        return // Don't show error for history, just skip
      }
      
      const response = await axios.get(
        `http://localhost:8000/api/admin/scraping/history?page=${historyPage}&page_size=10`,
        { 
          headers: { Authorization: `Bearer ${token}` }
          // Removed timeout to allow backend to take as long as needed
        }
      )
      setHistory(response.data.jobs || [])
      setHistoryTotalPages(response.data.total_pages || 1)
      setHistoryTotal(response.data.total || 0)
    } catch (error) {
      console.error('Failed to fetch history:', error)
      // Don't show alert for history errors
    } finally {
      setLoadingHistory(false)
    }
  }, [historyPage])
  
  const performDeleteHistory = async (jobId) => {
    isProcessingRef.current = true
    setDeletingHistoryId(jobId)
    
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      
      await axios.delete(
        `http://localhost:8000/api/admin/scraping/history/${jobId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      // Refresh history
      fetchHistory()
      showNotification('Scraping history deleted successfully', 'success')
    } catch (error) {
      console.error('Failed to delete history:', error)
      showNotification('Failed to delete history: ' + (error.response?.data?.detail || error.message), 'error')
    } finally {
      setDeletingHistoryId(null)
      setTimeout(() => {
        isProcessingRef.current = false
      }, 300)
    }
  }

  const handleDeleteHistory = useCallback(async (jobId) => {
    if (isProcessingRef.current) {
      return
    }
    
    showConfirmDialog(
      'Are you sure you want to delete this scraping history? This action cannot be undone.',
      () => {
        performDeleteHistory(jobId)
      }
    )
  }, [])

  const toggleBrandSelection = useCallback((brand) => {
    // Prevent rapid clicks
    const now = Date.now()
    if (now - lastClickTimeRef.current < 200) {
      return
    }
    lastClickTimeRef.current = now
    
    if (scraping || isProcessingRef.current) {
      return
    }
    
    setSelectedBrands(prev => {
      const exists = prev.some(b => b.brand_name === brand.brand_name && b.brand_url === brand.brand_url)
      if (exists) {
        return prev.filter(b => !(b.brand_name === brand.brand_name && b.brand_url === brand.brand_url))
      } else {
        return [...prev, brand]
      }
    })
  }, [scraping])

  const startScraping = useCallback(async () => {
    // Prevent multiple clicks
    if (isProcessingRef.current || scraping) {
      return
    }
    
    if (selectedBrands.length === 0) {
      showNotification('Please select at least one brand', 'error')
      return
    }

    isProcessingRef.current = true
    
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
      fetchHistory() // Refresh history only when starting new job
    } catch (error) {
      console.error('Failed to start scraping:', error)
      showNotification('Failed to start scraping: ' + (error.response?.data?.detail || error.message), 'error')
      isProcessingRef.current = false
    } finally {
      // Reset after a short delay
      setTimeout(() => {
        isProcessingRef.current = false
      }, 500)
    }
  }, [selectedBrands, scraping, fetchHistory])

  const checkScrapingStatus = useCallback(async () => {
    if (!currentJob || isProcessingRef.current) return
    
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const response = await axios.get(
        `http://localhost:8000/api/admin/scraping/status/${currentJob}`,
        { 
          headers: { Authorization: `Bearer ${token}` }
          // Removed timeout for status checks
        }
      )

      setJobStatus(response.data)

      if (response.data.status === 'completed') {
        setScraping(false)
        showNotification(`Scraping completed! ${response.data.products_added} products added`, 'success')
        fetchBrands()
        fetchHistory() // Refresh history only when job completes
        setSelectedBrands([])
        setCurrentJob(null)
        isProcessingRef.current = false
      } else if (response.data.status === 'failed') {
        setScraping(false)
        showNotification('Scraping failed: ' + (response.data.error || 'Unknown error'), 'error')
        fetchHistory() // Refresh history only when job fails
        setCurrentJob(null)
        isProcessingRef.current = false
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
        isProcessingRef.current = false
      }
    }
  }, [currentJob, fetchHistory])

  // useEffects after function definitions
  useEffect(() => {
    fetchBrands()
  }, [brandType])
  
  useEffect(() => {
    fetchHistory()
  }, [historyPage, fetchHistory])
  
  useEffect(() => {
    if (currentJob && scraping) {
      const interval = setInterval(() => {
        checkScrapingStatus()
      }, 3000) // Increased to 3 seconds to reduce load
      return () => clearInterval(interval)
    }
  }, [currentJob, scraping, checkScrapingStatus])
  
  // Refresh history only when page changes or after scraping completes
  // Removed periodic refresh to improve performance

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
              onChange={() => {}}
              disabled={scraping}
            />
            Local Affordable Brands
          </label>
        </div>
      </div>

      {/* Brand Selection */}
      <div className="section-card">
        <h3>Select Brands to Rescrape ({brandType})</h3>
        {loadingBrands ? (
          <p style={{ color: '#666', padding: '20px', textAlign: 'center' }}>
            Loading brands... Please wait.
          </p>
        ) : brands.length === 0 ? (
          <p style={{ color: '#999', padding: '20px' }}>
            No brands found for this type. Make sure Excel files are in the project root.
          </p>
        ) : (
          <>
            {/* Separate Men's and Women's Brands */}
            {(() => {
              // Strict separation based on gender field only
              // Women's dataset brands → gender="w"
              // CSV brands → gender="m"
              const mensBrands = brands.filter(b => b.gender === 'm')
              const womensBrands = brands.filter(b => b.gender === 'w')
              const otherBrands = brands.filter(b => b.gender !== 'm' && b.gender !== 'w')
              
              // Debug: log counts
              console.log('Total brands:', brands.length)
              console.log('Men\'s brands (gender="m"):', mensBrands.length)
              console.log('Women\'s brands (gender="w"):', womensBrands.length)
              if (mensBrands.length > 0) {
                console.log('Sample men\'s brands:', mensBrands.slice(0, 3).map(b => ({ name: b.brand_name, gender: b.gender, category: b.category })))
              }
              if (womensBrands.length > 0) {
                console.log('Sample women\'s brands:', womensBrands.slice(0, 3).map(b => ({ name: b.brand_name, gender: b.gender, category: b.category })))
              }
              
              return (
                <>
                  {/* Women's Brands Section */}
                  {womensBrands.length > 0 && (
                    <div style={{ marginBottom: '30px' }}>
                      <h4 style={{ marginBottom: '15px', fontSize: '1.2rem', fontWeight: '600', color: '#000', borderBottom: '2px solid #000', paddingBottom: '8px' }}>
                        Women's Brands ({womensBrands.length})
                      </h4>
                      <div className="brand-grid">
                        {womensBrands.map((brand, idx) => {
                          const isSelected = selectedBrands.some(
                            b => b.brand_name === brand.brand_name && b.brand_url === brand.brand_url
                          )
                          return (
                            <div
                              key={`${brand.brand_name}-${brand.brand_url}-${idx}`}
                              className={`brand-card ${isSelected ? 'selected' : ''}`}
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                if (!scraping && !isProcessingRef.current) {
                                  toggleBrandSelection(brand)
                                }
                              }}
                              style={{ cursor: scraping ? 'not-allowed' : 'pointer' }}
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
                    </div>
                  )}
                  
                  {/* Men's Brands Section */}
                  {mensBrands.length > 0 && (
                    <div style={{ marginBottom: '30px' }}>
                      <h4 style={{ marginBottom: '15px', fontSize: '1.2rem', fontWeight: '600', color: '#000', borderBottom: '2px solid #000', paddingBottom: '8px' }}>
                        Men's Brands ({mensBrands.length})
                      </h4>
                      <div className="brand-grid">
                        {mensBrands.map((brand, idx) => {
                          const isSelected = selectedBrands.some(
                            b => b.brand_name === brand.brand_name && b.brand_url === brand.brand_url
                          )
                          return (
                            <div
                              key={`${brand.brand_name}-${brand.brand_url}-${idx}`}
                              className={`brand-card ${isSelected ? 'selected' : ''}`}
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                if (!scraping && !isProcessingRef.current) {
                                  toggleBrandSelection(brand)
                                }
                              }}
                              style={{ cursor: scraping ? 'not-allowed' : 'pointer' }}
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
                    </div>
                  )}
                  
                  {/* Other Brands Section (if any) */}
                  {otherBrands.length > 0 && (
                    <div style={{ marginBottom: '30px' }}>
                      <h4 style={{ marginBottom: '15px', fontSize: '1.2rem', fontWeight: '600', color: '#000', borderBottom: '2px solid #000', paddingBottom: '8px' }}>
                        Other Brands ({otherBrands.length})
                      </h4>
                      <div className="brand-grid">
                        {otherBrands.map((brand, idx) => {
                          const isSelected = selectedBrands.some(
                            b => b.brand_name === brand.brand_name && b.brand_url === brand.brand_url
                          )
                          return (
                            <div
                              key={`${brand.brand_name}-${brand.brand_url}-${idx}`}
                              className={`brand-card ${isSelected ? 'selected' : ''}`}
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                if (!scraping && !isProcessingRef.current) {
                                  toggleBrandSelection(brand)
                                }
                              }}
                              style={{ cursor: scraping ? 'not-allowed' : 'pointer' }}
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
                    </div>
                  )}
                </>
              )
            })()}

            <div className="selection-actions">
          <p>{selectedBrands.length} brand(s) selected</p>
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              if (!isProcessingRef.current && !scraping && selectedBrands.length > 0) {
                startScraping()
              }
            }}
            disabled={scraping || selectedBrands.length === 0 || isProcessingRef.current}
            className="scrape-btn"
            style={{ pointerEvents: scraping || selectedBrands.length === 0 || isProcessingRef.current ? 'none' : 'auto' }}
          >
            {scraping ? 'Scraping in Progress...' : isProcessingRef.current ? 'Starting...' : 'Start Scraping'}
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3>Scraping History ({historyTotal} total)</h3>
        </div>
        
        {loadingHistory ? (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            Loading history... Please wait.
          </p>
        ) : history.length === 0 ? (
          <p>No scraping history yet.</p>
        ) : (
          <>
            <div className="history-list">
              {history.map((job, idx) => {
                // Format brand names properly
                const brandNames = job.brands?.map(b => 
                  typeof b === 'object' ? (b.brand_name || b) : b
                ).join(', ') || 'N/A'
                
                return (
                  <div key={job.job_id || idx} className="history-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', padding: '15px', border: '1px solid #e0e0e0', borderRadius: '4px' }}>
                    <div style={{ flex: 1 }}>
                      <div className="history-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span className={`history-status ${job.status}`} style={{ 
                          padding: '4px 12px', 
                          borderRadius: '4px', 
                          background: job.status === 'completed' ? '#000' : job.status === 'failed' ? '#ef4444' : '#666',
                          color: '#fff',
                          fontSize: '0.85rem',
                          fontWeight: '600'
                        }}>
                          {job.status?.toUpperCase() || 'UNKNOWN'}
                        </span>
                      </div>
                      <div className="history-details" style={{ display: 'flex', gap: '15px', fontSize: '0.9rem', color: '#666' }}>
                        <span>Brands: {brandNames}</span>
                        {job.products_added !== undefined && (
                          <span>Products Added: {job.products_added}</span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        if (!isProcessingRef.current && deletingHistoryId !== job.job_id) {
                          handleDeleteHistory(job.job_id)
                        }
                      }}
                      disabled={deletingHistoryId === job.job_id || isProcessingRef.current}
                      style={{
                        marginLeft: '15px',
                        padding: '6px 12px',
                        background: '#000',
                        color: '#fff',
                        border: '1px solid #fff',
                        borderRadius: '4px',
                        cursor: deletingHistoryId === job.job_id || isProcessingRef.current ? 'not-allowed' : 'pointer',
                        opacity: deletingHistoryId === job.job_id || isProcessingRef.current ? 0.6 : 1,
                        fontSize: '0.85rem',
                        fontWeight: '500',
                        transition: 'none',
                        pointerEvents: deletingHistoryId === job.job_id || isProcessingRef.current ? 'none' : 'auto'
                      }}
                    >
                      {deletingHistoryId === job.job_id ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                )
              })}
            </div>
            
            {/* Pagination */}
            {historyTotalPages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '10px', marginTop: '20px' }}>
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    if (!isProcessingRef.current && historyPage > 1) {
                      setHistoryPage(p => Math.max(1, p - 1))
                    }
                  }}
                  disabled={historyPage === 1 || isProcessingRef.current}
                  style={{
                    padding: '8px 16px',
                    background: historyPage === 1 || isProcessingRef.current ? '#ccc' : '#000',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: historyPage === 1 || isProcessingRef.current ? 'not-allowed' : 'pointer',
                    transition: 'none',
                    pointerEvents: historyPage === 1 || isProcessingRef.current ? 'none' : 'auto'
                  }}
                >
                  Previous
                </button>
                <span style={{ padding: '8px 16px' }}>
                  Page {historyPage} of {historyTotalPages}
                </span>
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    if (!isProcessingRef.current && historyPage < historyTotalPages) {
                      setHistoryPage(p => Math.min(historyTotalPages, p + 1))
                    }
                  }}
                  disabled={historyPage === historyTotalPages || isProcessingRef.current}
                  style={{
                    padding: '8px 16px',
                    background: historyPage === historyTotalPages || isProcessingRef.current ? '#ccc' : '#000',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: historyPage === historyTotalPages || isProcessingRef.current ? 'not-allowed' : 'pointer',
                    transition: 'none',
                    pointerEvents: historyPage === historyTotalPages || isProcessingRef.current ? 'none' : 'auto'
                  }}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default ScrapingManagement

