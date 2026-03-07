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
  const [cleanupProgress, setCleanupProgress] = useState(null) // Track cleanup progress

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
        // Filter for men's catalogue - filter by gender 'm'
        params.append('gender', 'm')
      } else if (categoryFilter === 'womens_catalogue') {
        // Filter for women's catalogue - filter by gender 'w'
        params.append('gender', 'w')
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
      setCleanupProgress({ status: 'checking', message: 'Checking all product image URLs...' })
      
      const response = await axios.post(
        'http://localhost:8000/api/admin/products/cleanup-links',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      setCleanupProgress({ status: 'processing', message: `Checked ${response.data.total} products...` })

      // Fetch broken links
      console.log('Cleanup response:', response.data)
      if (response.data.broken > 0) {
        try {
          // Fetch broken links with retry
          const brokenProductsResponse = await axios.get(
            `http://localhost:8000/api/admin/products?broken_links_only=true&page_size=1000`,
            { headers: { Authorization: `Bearer ${token}` } }
          )
          console.log('Broken links fetched:', brokenProductsResponse.data.products?.length || 0)
          const brokenProducts = brokenProductsResponse.data.products || []
          setBrokenLinks(brokenProducts)
          setShowBrokenLinks(true)
          
          // Show notification
          if (brokenProducts.length > 0) {
            showNotification(`Found ${brokenProducts.length} broken image links`, 'info')
          } else {
            showNotification(`Found ${response.data.broken} broken links but couldn't fetch details`, 'warning')
            setShowBrokenLinks(true) // Still show section
          }
        } catch (err) {
          console.error('Failed to fetch broken links:', err)
          // Show broken links section even if fetch fails, with count from response
          setBrokenLinks([])
          setShowBrokenLinks(true)
          showNotification(`Found ${response.data.broken} broken links but couldn't fetch details. Please try again.`, 'warning')
        }
      } else {
        setBrokenLinks([])
        setShowBrokenLinks(false)
        showNotification('All image URLs are working!', 'success')
      }
      
      fetchProducts()
    } catch (error) {
      console.error('Failed to cleanup links:', error)
      showNotification('Failed to cleanup links', 'error')
      setCleanupProgress(null)
    } finally {
      setLoading(false)
      setTimeout(() => setCleanupProgress(null), 2000) // Clear progress after 2 seconds
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
      background: ${type === 'success' ? '#10b981' : '#EF4444'};
      color: #fff;
      border: 2px solid ${type === 'success' ? '#059669' : '#EF4444'};
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
      background: #EF4444;
      color: #fff;
      border: 1px solid #EF4444;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
    `
    confirmBtn.onmouseover = () => confirmBtn.style.background = '#EF4444'
    confirmBtn.onmouseout = () => confirmBtn.style.background = '#EF4444'
    
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
            className="action-btn danger"
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
        <button onClick={handleCleanupLinks} className="action-btn danger" disabled={loading}>
          {loading ? 'Checking...' : 'Check Broken Links'}
        </button>
        
        {/* Cleanup Progress */}
        {cleanupProgress && (
          <div className="cleanup-progress-section" style={{ 
            marginTop: '20px',
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.05)',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <h4 style={{ marginBottom: '15px', fontSize: '1.1rem', color: '#fff' }}>
              Cleanup Progress
            </h4>
            <p style={{ color: '#fff', marginBottom: '15px', opacity: 0.9 }}>
              {cleanupProgress.message}
            </p>
            <div className="progress-bar" style={{ 
              width: '100%',
              height: '8px',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div 
                className="progress-fill" 
                style={{ 
                  width: cleanupProgress.status === 'checking' ? '50%' : '100%',
                  height: '100%',
                  background: 'linear-gradient(90deg, #ef4444, #dc2626)',
                  transition: 'width 0.5s ease',
                  animation: cleanupProgress.status === 'checking' ? 'pulse 1.5s ease-in-out infinite' : 'none'
                }}
              />
            </div>
          </div>
        )}
        
        {/* Broken Links List */}
        {showBrokenLinks && (
          <div className="broken-links-section" style={{ marginTop: '20px' }}>
            {brokenLinks.length > 0 ? (
              <>
                <h4 style={{ marginBottom: '15px', fontSize: '1.1rem', color: '#fff' }}>
                  Broken Image Links ({brokenLinks.length})
                </h4>
                <p style={{ marginBottom: '15px', fontSize: '0.9rem', color: '#fff', opacity: 0.8 }}>
                  These products have broken image URLs and are hidden from the product catalogue. You can repair or delete them.
                </p>
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
              </>
            ) : (
              <div style={{ padding: '15px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '4px', color: '#fff', opacity: 0.9 }}>
                <h4 style={{ marginBottom: '10px', fontSize: '1.1rem', color: '#fff' }}>
                  Broken Links Check Completed
                </h4>
                <p>No broken links found in the database. All image URLs are working.</p>
                <p style={{ marginTop: '10px', fontSize: '0.9rem', opacity: 0.8 }}>
                  Note: Products with broken image links are automatically hidden from the product catalogue.
                </p>
              </div>
            )}
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
            onClick={() => {
              // Filter for men's catalogue - products from men's brands
              setCategoryFilter('mens_catalogue')
              setPage(1)
            }}
          >
            Men
          </button>
          <button
            className={`category-tag ${categoryFilter === 'womens_catalogue' ? 'active' : ''}`}
            onClick={() => {
              // Filter for women's catalogue - products from women's brands
              setCategoryFilter('womens_catalogue')
              setPage(1)
            }}
          >
            Women
          </button>
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
                // Inline placeholder (no network) so it works when DNS/proxy fails
                const NO_IMAGE_DATA_URI = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#374151" width="200" height="200"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#9ca3af" font-size="14" font-family="sans-serif">No image</text></svg>')
                // Prefer local downloaded image; then image_url + proxy; never use external placeholder URL (causes proxy/DNS errors)
                const localPath = product.image_path && (product.image_path.startsWith('product_images/') || product.image_path.includes('product_images'))
                const localUrl = localPath ? `http://localhost:8000/data/${product.image_path.replace(/\\/g, '/')}` : null
                let rawUrl = localUrl || product.image_url || (product.image_path && !product.image_path.startsWith('http') ? `http://localhost:8000/data/${product.image_path.replace(/\\/g, '/')}` : product.image_path) || null
                if (rawUrl && (rawUrl.toLowerCase().includes('loader') || rawUrl.toLowerCase().includes('lazyload') || rawUrl.endsWith('.gif'))) rawUrl = null
                if (rawUrl && (rawUrl.includes('via.placeholder.com') || rawUrl.includes('placeholder'))) rawUrl = null
                const isExternal = rawUrl && /^https?:\/\//i.test(rawUrl) && !rawUrl.includes('localhost:8000')
                const imageUrl = isExternal
                  ? `http://localhost:8000/api/products/image-proxy?url=${encodeURIComponent(rawUrl)}`
                  : (rawUrl || NO_IMAGE_DATA_URI)
                // Fallback: if primary image fails, try product.image_url via proxy (when not placeholder/loader)
                const fallbackRaw = product.image_url && !/loader|lazyload|\.gif|via\.placeholder|placeholder/i.test(product.image_url)
                const fallbackProxyUrl = fallbackRaw && /^https?:\/\//i.test(product.image_url)
                  ? `http://localhost:8000/api/products/image-proxy?url=${encodeURIComponent(product.image_url)}`
                  : null
                
                return (
                  <div key={product._id} className="product-card-item" style={{ position: 'relative' }}>
                    <button
                      onClick={() => handleDeleteLink(product._id)}
                      className="product-delete-icon"
                      title="Delete product"
                      style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
                        border: 'none',
                        borderRadius: '50%',
                        width: '32px',
                        height: '32px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        zIndex: 10,
                        boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        color: '#fff',
                        fontSize: '16px',
                        fontWeight: 'bold'
                      }}
                    >
                      ×
                    </button>
                    <div className="product-image-wrapper">
                      <img
                        src={imageUrl}
                        alt={product.name}
                        className="product-image-small"
                        onError={(e) => {
                          const img = e.target
                          img.onerror = null
                          // If local/proxy failed, try product.image_url via proxy once before "No image"
                          if (fallbackProxyUrl && img.src !== fallbackProxyUrl) {
                            img.src = fallbackProxyUrl
                            return
                          }
                          img.src = NO_IMAGE_DATA_URI
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
            <div className="pagination" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '20px', marginTop: '30px' }}>
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
                className="pagination-btn"
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages} ({totalProducts} total)
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages || loading}
                className="pagination-btn"
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default ProductManagement

