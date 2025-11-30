import { useState, useEffect } from 'react'
import axios from 'axios'

function ProductManagement() {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [csvFile, setCsvFile] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(null)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [brokenLinksOnly, setBrokenLinksOnly] = useState(false)
  const [page, setPage] = useState(1)
  const [totalProducts, setTotalProducts] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [brokenLinks, setBrokenLinks] = useState([])
  const [showBrokenLinks, setShowBrokenLinks] = useState(false)
  const [repairingId, setRepairingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [recentlyImported, setRecentlyImported] = useState([])
  const [showImportedData, setShowImportedData] = useState(false)
  const [failedImages, setFailedImages] = useState(new Set()) // Track products with failed image loads

  useEffect(() => {
    fetchProducts()
    fetchCategories()
  }, [page, categoryFilter, brokenLinksOnly])
  
  // Reset failed images when products change (e.g., after repair)
  useEffect(() => {
    // Clear failed images for products that are no longer in the list
    // This helps show repaired products
    setFailedImages(prev => {
      const productIds = new Set(products.map(p => p._id))
      return new Set([...prev].filter(id => productIds.has(id)))
    })
  }, [products])

  const fetchProducts = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      
      if (!token) {
        console.error('No token found in ProductManagement')
        setLoading(false)
        return
      }
      
      console.log('ProductManagement - Token found:', token.substring(0, 20) + '...')
      
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20'
      })
      
      if (categoryFilter === 'mens_catalogue') {
        // Special filter for men's catalogue - filter by gender
        params.append('gender', 'm')
      } else if (categoryFilter) {
        params.append('category', categoryFilter)
      }
      if (brokenLinksOnly) params.append('broken_links_only', 'true')

      console.log('ProductManagement - Making request to:', `http://localhost:8000/api/admin/products?${params}`)
      
      const response = await axios.get(
        `http://localhost:8000/api/admin/products?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      const allProducts = response.data.products || []
      // Filter out broken links for display
      const validProducts = allProducts.filter(p => !p.broken_link)
      setProducts(validProducts)
      // Count only valid products (without broken links)
      setTotalProducts(response.data.total || 0)
      // Calculate total pages if not provided
      const calculatedTotalPages = response.data.total_pages || 
        Math.ceil((response.data.total || 0) / 20)
      setTotalPages(calculatedTotalPages)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch products:', error)
      console.error('Error response:', error.response?.data)
      console.error('Error status:', error.response?.status)
      setLoading(false)
    }
  }

  const fetchCategories = async () => {
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      
      if (!token) {
        console.error('No token found in ProductManagement (categories)')
        return
      }
      
      const response = await axios.get(
        'http://localhost:8000/api/admin/categories',
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setCategories(response.data.categories)
    } catch (error) {
      console.error('Failed to fetch categories:', error)
      console.error('Error response:', error.response?.data)
    }
  }

  const handleCSVUpload = async (e) => {
    e.preventDefault()
    if (!csvFile) {
      alert('Please select a CSV file')
      return
    }

    const formData = new FormData()
    formData.append('file', csvFile)

    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      setUploadProgress('Uploading...')
      
      const response = await axios.post(
        'http://localhost:8000/api/admin/products/import-csv',
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      setUploadProgress(null)
      
      // Show detailed results
      let message = `Import completed! Total Rows: ${response.data.total_rows}, Imported: ${response.data.imported}, Failed: ${response.data.failed}`
      
      // Show errors if any
      if (response.data.errors && response.data.errors.length > 0) {
        message += `. Errors: ${response.data.errors.slice(0, 5).join(', ')}`
        if (response.data.errors.length > 5) {
          message += ` and ${response.data.errors.length - 5} more`
        }
      }
      
      showNotification(message, response.data.failed > 0 ? 'error' : 'success')
      setCsvFile(null)
      
      // Fetch and show recently imported products
      if (response.data.imported > 0) {
        // Fetch the latest products (recently imported)
        try {
          const productsResponse = await axios.get(
            `http://localhost:8000/api/admin/products?page=1&page_size=${response.data.imported}`,
            { headers: { Authorization: `Bearer ${token}` } }
          )
          // Get the most recent products (assuming they're sorted by created_at desc)
          const importedProducts = (productsResponse.data.products || []).slice(0, response.data.imported)
          setRecentlyImported(importedProducts)
          setShowImportedData(true)
        } catch (err) {
          console.error('Failed to fetch imported products:', err)
        }
      }
      
      fetchProducts()
      fetchCategories()
    } catch (error) {
      setUploadProgress(null)
      console.error('Failed to upload CSV:', error)
      const errorMsg = error.response?.data?.detail || error.message
      showNotification(`Failed to upload CSV: ${errorMsg}`, 'error')
    }
  }

  const handleCleanupLinks = async () => {
    showConfirmDialog(
      'This will check all product image URLs. Continue?',
      async () => {
        // User confirmed, proceed with cleanup
        await performCleanupLinks()
      }
    )
  }

  const performCleanupLinks = async () => {

    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      setLoading(true)
      
      const response = await axios.post(
        'http://localhost:8000/api/admin/products/cleanup-links',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Fetch broken links
      if (response.data.broken > 0 && response.data.broken_ids) {
        const brokenProductsResponse = await axios.get(
          `http://localhost:8000/api/admin/products?broken_links_only=true&page_size=100`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        setBrokenLinks(brokenProductsResponse.data.products || [])
        setShowBrokenLinks(true)
      } else {
        setBrokenLinks([])
        setShowBrokenLinks(false)
      }
      
      fetchProducts()
    } catch (error) {
      console.error('Failed to cleanup links:', error)
      showNotification('Failed to cleanup links', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleRepairLink = async (productId) => {
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      setRepairingId(productId)
      
      const response = await axios.post(
        `http://localhost:8000/api/admin/products/${productId}/repair-link`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )

      if (response.data.success) {
        // Show success notification
        showNotification('Link repaired successfully! Product will now appear in catalogue.', 'success')
        // Remove from broken links list
        setBrokenLinks(prev => prev.filter(p => p._id !== productId))
        // Clear from failed images so product can show up again
        setFailedImages(prev => {
          const newSet = new Set(prev)
          newSet.delete(productId)
          return newSet
        })
        // Refresh products to show the repaired product
        fetchProducts()
        // Also refresh categories to update counts
        fetchCategories()
      } else {
        // Show failure notification
        showNotification('This link cannot be repaired', 'error')
      }
    } catch (error) {
      console.error('Failed to repair link:', error)
      showNotification('This link cannot be repaired', 'error')
    } finally {
      setRepairingId(null)
    }
  }

  const handleClearAllProducts = async () => {
    const confirmMessage = `Are you absolutely sure you want to delete ALL products from the catalogue?\n\nThis action cannot be undone!\n\nTotal products: ${totalProducts}`
    
    if (!confirm(confirmMessage)) {
      return
    }
    
    // Double confirmation
    if (!confirm('This is your last chance. Are you 100% sure you want to delete ALL products?')) {
      return
    }
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      
      if (!token) {
        showNotification('Authentication required', 'error')
        return
      }
      
      const response = await axios.delete(
        'http://localhost:8000/api/admin/products/clear-all',
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      if (response.data.success) {
        showNotification(`Successfully cleared ${response.data.deleted_count} products from catalogue`, 'success')
        // Refresh products list
        setPage(1)
        fetchProducts()
        fetchCategories()
      } else {
        showNotification('Failed to clear products', 'error')
      }
    } catch (error) {
      console.error('Failed to clear products:', error)
      showNotification('Failed to clear products: ' + (error.response?.data?.detail || error.message), 'error')
    }
  }

  const handleDeleteLink = async (productId) => {
    showConfirmDialog(
      'Are you sure you want to delete this product? This action cannot be undone.',
      async () => {
        await performDeleteLink(productId)
      }
    )
  }

  const performDeleteLink = async (productId) => {

    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      setDeletingId(productId)
      
      await axios.delete(
        `http://localhost:8000/api/admin/products/${productId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Remove from broken links list
      setBrokenLinks(prev => prev.filter(p => p._id !== productId))
      // Refresh products
      fetchProducts()
      showNotification('Product deleted successfully', 'success')
    } catch (error) {
      console.error('Failed to delete product:', error)
      showNotification('Failed to delete product', 'error')
    } finally {
      setDeletingId(null)
    }
  }

  const showNotification = (message, type) => {
    // Create notification element
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
    
    // Remove after 3 seconds (no animation delay)
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
    // Create overlay
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
    
    // Create dialog
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
    
    // Message
    const messageEl = document.createElement('div')
    messageEl.textContent = message
    messageEl.style.cssText = `
      margin-bottom: 20px;
      font-size: 16px;
      color: #333;
      line-height: 1.5;
    `
    
    // Buttons container
    const buttonsContainer = document.createElement('div')
    buttonsContainer.style.cssText = `
      display: flex;
      gap: 10px;
      justify-content: flex-end;
    `
    
    // Cancel button
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
    
    // Confirm button
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
    
    // Event handlers
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
    
    // Assemble
    buttonsContainer.appendChild(cancelBtn)
    buttonsContainer.appendChild(confirmBtn)
    dialog.appendChild(messageEl)
    dialog.appendChild(buttonsContainer)
    overlay.appendChild(dialog)
    document.body.appendChild(overlay)
    
    // Close on overlay click
    overlay.onclick = (e) => {
      if (e.target === overlay) {
        close()
        if (onCancel) onCancel()
      }
    }
  }

  return (
    <div className="product-management">
      <div className="module-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <div>
            <h2>Product Catalogue Management</h2>
            <p>Import products, manage categories, and check image links</p>
          </div>
          <button
            onClick={handleClearAllProducts}
            className="action-btn"
            style={{
              backgroundColor: '#ef4444',
              color: '#fff',
              border: '2px solid #dc2626',
              padding: '10px 20px',
              fontSize: '0.9rem',
              fontWeight: '600',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.target.style.backgroundColor = '#dc2626'
            }}
            onMouseOut={(e) => {
              e.target.style.backgroundColor = '#ef4444'
            }}
          >
            Clear All Products ({totalProducts})
          </button>
        </div>
      </div>

      {/* CSV Upload Section */}
      <div className="section-card">
        <h3>Import Products from CSV</h3>
        <form onSubmit={handleCSVUpload} className="csv-upload-form">
          <div className="file-input-wrapper">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setCsvFile(e.target.files[0])}
              className="file-input"
              id="csvFile"
            />
            <label htmlFor="csvFile" className="file-label">
              {csvFile ? csvFile.name : 'Choose CSV file...'}
            </label>
          </div>
          <button type="submit" className="upload-btn" disabled={!csvFile || uploadProgress}>
            {uploadProgress || 'Upload CSV'}
          </button>
        </form>
        <div className="csv-info">
          <p><strong>CSV Format:</strong> name, category, brand, price, image_url, description</p>
        </div>
      </div>

      {/* Recently Imported Products Section */}
      {showImportedData && recentlyImported.length > 0 && (
        <div className="section-card" style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3>Recently Imported Products ({recentlyImported.length})</h3>
            <button 
              onClick={() => {
                setShowImportedData(false)
                setRecentlyImported([])
              }}
              className="action-btn"
              style={{ padding: '8px 16px', fontSize: '0.9rem' }}
            >
              Hide
            </button>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Brand</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th>Image URL</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {recentlyImported.map(product => (
                  <tr key={product._id || product.product_id}>
                    <td><strong>{product.name || 'N/A'}</strong></td>
                    <td>{product.brand || 'N/A'}</td>
                    <td>{product.category || 'N/A'}</td>
                    <td>PKR {product.price ? parseFloat(product.price).toFixed(2) : '0.00'}</td>
                    <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {product.image_url || product.image_path || 'N/A'}
                    </td>
                    <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {product.description || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Link Cleanup Section */}
      <div className="section-card">
        <h3>Image Link Cleanup</h3>
        <p>Check all product image URLs and mark broken links</p>
        <button onClick={handleCleanupLinks} className="cleanup-btn" disabled={loading}>
          {loading ? 'Checking...' : 'Check Broken Links'}
        </button>
        
        {/* Broken Links List */}
        {showBrokenLinks && brokenLinks.length > 0 && (
          <div className="broken-links-section" style={{ marginTop: '20px' }}>
            <h4 style={{ marginBottom: '15px', fontSize: '1.1rem' }}>
              Broken Links ({brokenLinks.length})
            </h4>
            <div className="broken-links-table">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Product Name</th>
                    <th>Image URL</th>
                    <th>Brand</th>
                    <th>Category</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {brokenLinks.map(product => (
                    <tr key={product._id}>
                      <td>{product.name}</td>
                      <td>
                        <span className="broken-url">
                          {product.image_url || product.image_path || 'N/A'}
                        </span>
                      </td>
                      <td>{product.brand || 'N/A'}</td>
                      <td>{product.category || 'N/A'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '10px' }}>
                          <button
                            onClick={() => handleRepairLink(product._id)}
                            className="repair-btn"
                            disabled={repairingId === product._id || deletingId === product._id}
                          >
                            {repairingId === product._id ? 'Repairing...' : 'Repair'}
                          </button>
                          <button
                            onClick={() => handleDeleteLink(product._id)}
                            className="delete-btn"
                            disabled={repairingId === product._id || deletingId === product._id}
                            style={{
                              background: '#000',
                              color: '#fff',
                              border: '1px solid #fff',
                              padding: '6px 12px',
                              borderRadius: '4px',
                              cursor: deletingId === product._id ? 'not-allowed' : 'pointer',
                              opacity: deletingId === product._id ? 0.6 : 1
                            }}
                          >
                            {deletingId === product._id ? 'Deleting...' : 'Delete'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {showBrokenLinks && brokenLinks.length === 0 && (
          <div style={{ marginTop: '15px', padding: '15px', background: '#f5f5f5', borderRadius: '4px', color: '#000' }}>
            No broken links found! All image URLs are working.
          </div>
        )}
      </div>

      {/* Categories Section */}
      <div className="section-card">
        <h3>Categories</h3>
        <div className="category-list">
          <button
            className={`category-tag ${categoryFilter === '' ? 'active' : ''}`}
            onClick={() => {
              setCategoryFilter('')
              setPage(1) // Reset to first page when filter changes
            }}
          >
            All ({totalProducts})
          </button>
          <button
            className={`category-tag ${categoryFilter === 'mens_catalogue' ? 'active' : ''}`}
            onClick={async () => {
              // Set a special filter for men's catalogue
              setCategoryFilter('mens_catalogue')
              setPage(1)
            }}
            style={{ 
              backgroundColor: categoryFilter === 'mens_catalogue' ? '#667eea' : '#f0f0f0',
              color: categoryFilter === 'mens_catalogue' ? '#fff' : '#000',
              fontWeight: categoryFilter === 'mens_catalogue' ? '600' : '400'
            }}
          >
            Men's Catalogue
          </button>
          {categories.map(cat => (
            <button
              key={cat.name}
              className={`category-tag ${categoryFilter === cat.name ? 'active' : ''}`}
              onClick={() => {
                setCategoryFilter(cat.name)
                setPage(1) // Reset to first page when filter changes
              }}
            >
              {cat.name} ({cat.count})
            </button>
          ))}
        </div>
      </div>

      {/* Products Grid */}
      <div className="section-card">
        <h3>Products</h3>

        {loading ? (
          <div className="loading">Loading products...</div>
        ) : products.length === 0 ? (
          <div className="no-products">No products found. Start scraping to add products!</div>
        ) : (
          <>
            <div className="products-grid">
              {products
                .filter(product => !product.broken_link && !failedImages.has(product._id)) // Hide products with broken links AND failed image loads
                .map(product => {
                // Build image URL for valid products only
                const imageUrl = product.image_url || 
                  (product.image_path ? `http://localhost:8000/data/${product.image_path.replace(/\\/g, '/')}` : null) ||
                  'https://via.placeholder.com/200?text=No+Image'
                
                return (
                  <div key={product._id} className="product-card-item">
                    <div className="product-image-wrapper">
                      <img
                        src={imageUrl}
                        alt={product.name}
                        className="product-image-small"
                        onError={(e) => {
                          // If image fails to load, hide the product from display
                          setFailedImages(prev => new Set([...prev, product._id]))
                          // Hide the product card immediately
                          if (e.target.closest('.product-card-item')) {
                            e.target.closest('.product-card-item').style.display = 'none'
                          }
                        }}
                        loading="lazy"
                      />
                    </div>
                    <div className="product-info-wrapper">
                      <div className="product-name-small">{product.name}</div>
                      <div className="product-brand-small">{product.brand || 'N/A'}</div>
                      <div className="product-meta">
                        <span className="product-category-small">{product.category}</span>
                        <span className="product-price-small">PKR {product.price ? parseFloat(product.price).toFixed(2) : '0.00'}</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="pagination-controls">
              <button
                onClick={() => setPage(1)}
                disabled={page === 1 || loading}
                className="pagination-btn"
                title="First page"
              >
                ««
              </button>
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
                className="pagination-btn"
                title="Previous page"
              >
                «
              </button>
              
              <div className="page-numbers">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (page <= 3) {
                    pageNum = i + 1;
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = page - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      disabled={loading}
                      className={`page-number-btn ${page === pageNum ? 'active' : ''}`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages || loading}
                className="pagination-btn"
                title="Next page"
              >
                »
              </button>
              <button
                onClick={() => setPage(totalPages)}
                disabled={page === totalPages || loading}
                className="pagination-btn"
                title="Last page"
              >
                »»
              </button>
              
              <span className="page-info">
                Page {page} of {totalPages} ({totalProducts} total)
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default ProductManagement

