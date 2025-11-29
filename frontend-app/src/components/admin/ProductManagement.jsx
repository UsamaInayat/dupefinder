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

  useEffect(() => {
    fetchProducts()
    fetchCategories()
  }, [page, categoryFilter, brokenLinksOnly])

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
      
      if (categoryFilter) params.append('category', categoryFilter)
      if (brokenLinksOnly) params.append('broken_links_only', 'true')

      console.log('ProductManagement - Making request to:', `http://localhost:8000/api/admin/products?${params}`)
      
      const response = await axios.get(
        `http://localhost:8000/api/admin/products?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setProducts(response.data.products || [])
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
      let message = `Import completed!\n\nTotal Rows: ${response.data.total_rows}\nImported: ${response.data.imported}\nFailed: ${response.data.failed}`
      
      // Show errors if any
      if (response.data.errors && response.data.errors.length > 0) {
        message += `\n\nErrors:\n${response.data.errors.slice(0, 10).join('\n')}`
        if (response.data.errors.length > 10) {
          message += `\n... and ${response.data.errors.length - 10} more errors`
        }
      }
      
      alert(message)
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
      alert(`Failed to upload CSV:\n${errorMsg}`)
    }
  }

  const handleCleanupLinks = async () => {
    if (!confirm('This will check all product image URLs. Continue?')) return

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
      alert('Failed to cleanup links')
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
        showNotification('Link repaired successfully!', 'success')
        // Remove from broken links list
        setBrokenLinks(prev => prev.filter(p => p._id !== productId))
        // Refresh products
        fetchProducts()
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

  const handleDeleteLink = async (productId) => {
    if (!confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
      return
    }

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

  return (
    <div className="product-management">
      <div className="module-header">
        <h2>Product Catalogue Management</h2>
        <p>Import products, manage categories, and check image links</p>
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
                    <td>PKR {product.price ? (parseFloat(product.price) * 280).toFixed(2) : '0.00'}</td>
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
              {products.map(product => {
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
                          e.target.src = 'https://via.placeholder.com/200?text=No+Image'
                        }}
                      />
                      {product.broken_link && (
                        <span className="broken-link-badge">Broken</span>
                      )}
                    </div>
                    <div className="product-info-wrapper">
                      <div className="product-name-small">{product.name}</div>
                      <div className="product-brand-small">{product.brand || 'N/A'}</div>
                      <div className="product-meta">
                        <span className="product-category-small">{product.category}</span>
                        <span className="product-price-small">PKR {product.price ? (parseFloat(product.price) * 280).toFixed(2) : '0.00'}</span>
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

