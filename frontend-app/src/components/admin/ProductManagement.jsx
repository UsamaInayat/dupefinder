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
      alert(`Import completed!\nImported: ${response.data.imported}\nFailed: ${response.data.failed}`)
      setCsvFile(null)
      fetchProducts()
    } catch (error) {
      setUploadProgress(null)
      console.error('Failed to upload CSV:', error)
      alert('Failed to upload CSV: ' + (error.response?.data?.detail || error.message))
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

      alert(`Cleanup completed!\nChecked: ${response.data.checked}\nBroken: ${response.data.broken}\nWorking: ${response.data.working}`)
      fetchProducts()
    } catch (error) {
      console.error('Failed to cleanup links:', error)
      alert('Failed to cleanup links')
    } finally {
      setLoading(false)
    }
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

      {/* Link Cleanup Section */}
      <div className="section-card">
        <h3>Image Link Cleanup</h3>
        <p>Check all product image URLs and mark broken links</p>
        <button onClick={handleCleanupLinks} className="cleanup-btn" disabled={loading}>
          {loading ? 'Checking...' : 'Check Broken Links'}
        </button>
      </div>

      {/* Categories Section */}
      <div className="section-card">
        <h3>Categories</h3>
        <div className="category-list">
          {categories.map(cat => (
            <span key={cat.name} className="category-tag">
              {cat.name} ({cat.count})
            </span>
          ))}
        </div>
      </div>

      {/* Products Table */}
      <div className="section-card">
        <div className="table-header">
          <h3>Products</h3>
          <div className="table-filters">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="filter-select"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.name} value={cat.name}>{cat.name}</option>
              ))}
            </select>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={brokenLinksOnly}
                onChange={(e) => setBrokenLinksOnly(e.target.checked)}
              />
              Broken Links Only
            </label>
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading products...</div>
        ) : products.length === 0 ? (
          <div className="no-products">No products found. Start scraping to add products!</div>
        ) : (
          <>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Image</th>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Brand</th>
                    <th>Price</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(product => (
                    <tr key={product._id}>
                      <td>
                        <img
                          src={product.image_url || product.image_path || 'https://via.placeholder.com/50?text=No+Image'}
                          alt={product.name}
                          className="product-thumb"
                          onError={(e) => {
                            e.target.src = 'https://via.placeholder.com/50?text=No+Image'
                          }}
                        />
                      </td>
                      <td>
                        <div className="product-name-cell">
                          <strong>{product.name}</strong>
                          {product.description && (
                            <small className="product-desc">{product.description.substring(0, 50)}...</small>
                          )}
                        </div>
                      </td>
                      <td><span className="category-badge">{product.category}</span></td>
                      <td>{product.brand || 'N/A'}</td>
                      <td>${product.price || '0.00'}</td>
                      <td>
                        {product.broken_link ? (
                          <span className="status-badge broken">Broken Link</span>
                        ) : (
                          <span className="status-badge ok">OK</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination-controls">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
                className="pagination-btn"
              >
                Previous
              </button>
              <span className="page-info">
                Page {page} ({totalProducts} total products)
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={products.length < 20 || loading}
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

