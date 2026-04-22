import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { adminApiUrl } from '../../lib/adminApiUrl'
import { apiUrl, publicDataUrl, isOurApiAbsoluteUrl } from '../../lib/apiBase'

function ProductManagement() {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [csvFile, setCsvFile] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(null)
  const [genderFilter, setGenderFilter] = useState('') // '' = All, 'w' = Women, 'm' = Men
  const [categoryFilter, setCategoryFilter] = useState('') // '' = All, else category name from API
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
  const productsLoadedRef = useRef(false)

  useEffect(() => {
    const silent = productsLoadedRef.current
    ;(async () => {
      await fetchProducts({ silent })
      productsLoadedRef.current = true
    })()
  }, [page, genderFilter, categoryFilter, brokenLinksOnly])

  // Fetch categories when gender changes (categories are per-gender for dropdown)
  useEffect(() => {
    fetchCategories()
  }, [genderFilter])
  
  // Reset failed images when products change (e.g., after repair)
  useEffect(() => {
    // Clear failed images for products that are no longer in the list
    // This helps show repaired products
    setFailedImages(prev => {
      const productIds = new Set(products.map(p => p._id))
      return new Set([...prev].filter(id => productIds.has(id)))
    })
  }, [products])

  // Strip "(70)" / "(81)" from category so "Women Short Kurti (70)" → "Women Short Kurti"
  const normalizeCategory = (cat) => (cat || '').replace(/\s*\(\d+\)\s*$/, '').trim()

  const fetchProducts = async (opts = {}) => {
    const { silent = false } = opts
    if (!silent) setLoading(true)
    const currentGender = genderFilter
    const rawCategory = categoryFilter
    const currentCategory = normalizeCategory(rawCategory)
    const isMergedLuxe = (currentCategory || '').toLowerCase() === 'women luxe'
    const isMergedShortKurti = (currentCategory || '').toLowerCase() === 'women short kurti'
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      if (!token) {
        return
      }
      const headers = { Authorization: `Bearer ${token}` }

      // Women Luxe & Women Short Kurti: only merged endpoint (guarantees correct total)
      if (isMergedLuxe || isMergedShortKurti) {
        const merged = isMergedLuxe ? 'women_luxe' : 'women_short_kurti'
        const url = adminApiUrl(
          `/products/merged?merged_category=${encodeURIComponent(merged)}&page=${page}&page_size=20`
        )
        const res = await axios.get(url, { headers })
        setProducts(res.data.products || [])
        setTotalProducts(res.data.total ?? 0)
        setTotalPages(res.data.total_pages ?? Math.ceil((res.data.total || 0) / 20))
        return
      }

      const params = new URLSearchParams({ page: page.toString(), page_size: '20' })
      if (currentGender) params.append('gender', currentGender)
      if (currentCategory) params.append('category', currentCategory)
      if (brokenLinksOnly) params.append('broken_links_only', 'true')

      const res = await axios.get(
        adminApiUrl(`/products?${params}`),
        { headers }
      )
      setProducts(res.data.products || [])
      setTotalProducts(res.data.total ?? 0)
      setTotalPages(res.data.total_pages ?? Math.ceil((res.data.total || 0) / 20))
    } catch (error) {
      console.error('Failed to fetch products:', error)
      console.error('Error response:', error.response?.data)
      console.error('Error status:', error.response?.status)
    } finally {
      if (!silent) setLoading(false)
    }
  }

  // Frontend merge: show Women Luxe / Women Short Kurti instead of raw slugs (so dropdown matches Women Kurta/Lawn)
  const normalizeCategoriesForDropdown = (list) => {
    if (!Array.isArray(list) || list.length === 0) return list
    const WOMEN_LUXE_SLUGS = ['bridal-in-stock', 'festive-in-stock', 'wedding-unstitched-2025']
    const WOMEN_SHORT_KURTI_SLUGS = ['ss-wesst', 'ss-west', 'short-kurti']
    const norm = (s) => (s || '').toLowerCase().replace(/\s+/g, '-').replace(/_/g, '-').trim()
    const merged = {}
    for (const c of list) {
      const name = (c && c.name) ? String(c.name).trim() : ''
      const count = typeof c.count === 'number' ? c.count : parseInt(c.count, 10) || 0
      if (!name) continue
      const n = norm(name)
      if (name === 'Women Luxe') {
        merged['Women Luxe'] = count
      } else if (name === 'Women Short Kurti') {
        merged['Women Short Kurti'] = count
      } else if (WOMEN_LUXE_SLUGS.some(slug => n === slug || n.includes(slug))) {
        merged['Women Luxe'] = (merged['Women Luxe'] || 0) + count
      } else if (WOMEN_SHORT_KURTI_SLUGS.some(slug => n === slug || n.includes(slug))) {
        merged['Women Short Kurti'] = (merged['Women Short Kurti'] || 0) + count
      } else {
        merged[name] = (merged[name] || 0) + count
      }
    }
    return Object.entries(merged).map(([n, cnt]) => ({ name: n, count: cnt })).sort((a, b) => a.name.localeCompare(b.name))
  }

  const fetchCategories = async () => {
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      if (!token) return
      const url = genderFilter
        ? adminApiUrl(`/categories?gender=${encodeURIComponent(genderFilter)}`)
        : adminApiUrl('/categories')
      const response = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } })
      const raw = response.data.categories || []
      setCategories(normalizeCategoriesForDropdown(raw))
    } catch (error) {
      console.error('Failed to fetch categories:', error)
      setCategories([])
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
        adminApiUrl('/products/import-csv'),
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
            adminApiUrl(`/products?page=1&page_size=${response.data.imported}`),
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
      
      fetchProducts({ silent: true })
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
        adminApiUrl('/products/cleanup-links'),
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
            adminApiUrl('/products?broken_links_only=true&page_size=1000'),
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
      
      fetchProducts({ silent: true })
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
        adminApiUrl(`/products/${productId}/repair-link`),
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
        fetchProducts({ silent: true })
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
        adminApiUrl('/products/clear-all'),
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      if (response.data.success) {
        showNotification(`Successfully cleared ${response.data.deleted_count} products from catalogue`, 'success')
        setPage(1)
        productsLoadedRef.current = false
        fetchCategories()
        await fetchProducts({ silent: false })
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
    const snapshot = products
    setProducts((prev) => prev.filter((p) => p._id !== productId))
    setBrokenLinks((prev) => prev.filter((p) => p._id !== productId))

    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      setDeletingId(productId)

      await axios.delete(adminApiUrl(`/products/${productId}`), {
        headers: { Authorization: `Bearer ${token}` },
      })

      showNotification('Product deleted successfully', 'success')
      fetchProducts({ silent: true })
    } catch (error) {
      console.error('Failed to delete product:', error)
      setProducts(snapshot)
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
      background: ${type === 'success' ? '#10b981' : '#e91e8c'};
      color: #fff;
      border: 2px solid ${type === 'success' ? '#059669' : '#c026d3'};
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
      background: linear-gradient(90deg, #e91e8c, #a855f7);
      color: #fff;
      border: 1px solid rgba(192, 38, 211, 0.5);
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
    `
    confirmBtn.onmouseover = () => { confirmBtn.style.background = 'linear-gradient(90deg, #c026d3, #7c3aed)' }
    confirmBtn.onmouseout = () => { confirmBtn.style.background = 'linear-gradient(90deg, #e91e8c, #a855f7)' }
    
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
            <p>Manage products and apply filters.</p>
          </div>
          <button
            onClick={handleClearAllProducts}
            className="action-btn danger"
          >
            Clear All Products ({totalProducts})
          </button>
        </div>
      </div>

      {/* Gender & Category dropdowns */}
      <div className="section-card">
        <h3>Filters</h3>
        <div className="category-list" style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
          <label style={{ fontWeight: 600 }}>Gender:</label>
          <select
            value={genderFilter}
            onChange={(e) => {
              setGenderFilter(e.target.value)
              setCategoryFilter('')
              setPage(1)
            }}
            style={{ padding: '8px 12px', borderRadius: '6px', minWidth: '120px' }}
          >
            <option value="">All</option>
            <option value="w">Women</option>
            <option value="m">Men</option>
          </select>
          <label style={{ fontWeight: 600, marginLeft: '8px' }}>Category:</label>
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(normalizeCategory(e.target.value) || e.target.value)
              setPage(1)
            }}
            style={{ padding: '8px 12px', borderRadius: '6px', minWidth: '200px' }}
          >
            <option value="">All categories</option>
            {categories.map((c) => {
              const optName = normalizeCategory(c.name) || c.name
              return (
                <option key={optName} value={optName}>
                  {optName} ({c.count})
                </option>
              )
            })}
          </select>
          <span style={{ color: '#6b7280', fontSize: '14px' }}>Total: {totalProducts}</span>
        </div>
      </div>

      {/* Products Grid */}
      <div className="section-card">
        <h3>Products</h3>

        {loading && products.length === 0 ? (
          <div className="loading">Loading products...</div>
        ) : products.length === 0 ? (
          <div className="no-products">No products found. Start scraping to add products!</div>
        ) : (
          <>
            <div
              className="products-grid"
              style={{ opacity: loading ? 0.55 : 1, transition: 'opacity 0.12s ease', pointerEvents: loading ? 'none' : 'auto' }}
            >
              {products
                .filter(product => !failedImages.has(product._id)) // Hide only those whose image failed to load in this session
                .map(product => {
                // Inline placeholder (no network) so it works when DNS/proxy fails
                const NO_IMAGE_DATA_URI = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#374151" width="200" height="200"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#9ca3af" font-size="14" font-family="sans-serif">No image</text></svg>')
                // Prefer local downloaded image; then image_url + proxy; never use external placeholder URL (causes proxy/DNS errors)
                const localPath = product.image_path && (product.image_path.startsWith('product_images/') || product.image_path.includes('product_images'))
                const normPath = product.image_path.replace(/\\/g, '/')
                const localUrl = localPath ? publicDataUrl(normPath) : null
                let rawUrl =
                  localUrl ||
                  product.image_url ||
                  (product.image_path && !product.image_path.startsWith('http') ? publicDataUrl(normPath) : product.image_path) ||
                  null
                if (rawUrl && (rawUrl.toLowerCase().includes('loader') || rawUrl.toLowerCase().includes('lazyload') || rawUrl.endsWith('.gif'))) rawUrl = null
                if (rawUrl && (rawUrl.includes('via.placeholder.com') || rawUrl.includes('placeholder'))) rawUrl = null
                const isExternal = rawUrl && /^https?:\/\//i.test(rawUrl) && !isOurApiAbsoluteUrl(rawUrl)
                const imageUrl = isExternal
                  ? apiUrl(`/api/products/image-proxy?url=${encodeURIComponent(rawUrl)}`)
                  : (rawUrl || NO_IMAGE_DATA_URI)
                // Fallback: if primary image fails, try product.image_url via proxy (when not placeholder/loader)
                const fallbackRaw = product.image_url && !/loader|lazyload|\.gif|via\.placeholder|placeholder/i.test(product.image_url)
                const fallbackProxyUrl = fallbackRaw && /^https?:\/\//i.test(product.image_url)
                  ? apiUrl(`/api/products/image-proxy?url=${encodeURIComponent(product.image_url)}`)
                  : null
                
                const productPageUrl = (product.product_url || product.product_link || '').trim()
                const canOpenProductPage = productPageUrl && /^https?:\/\//i.test(productPageUrl)
                const openProductPage = (e) => {
                  if (e.target.closest('button.product-delete-icon')) return
                  if (canOpenProductPage) window.open(productPageUrl, '_blank', 'noopener,noreferrer')
                }
                return (
                  <div key={product._id} className="product-card-item" style={{ position: 'relative' }}>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleDeleteLink(product._id); }}
                      className="product-delete-icon"
                      title="Delete product"
                      style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        zIndex: 10,
                        cursor: 'pointer',
                      }}
                    >
                      ×
                    </button>
                    <div
                      className="product-image-wrapper"
                      onClick={openProductPage}
                      role={canOpenProductPage ? 'button' : undefined}
                      title={canOpenProductPage ? 'View product on brand site' : (productPageUrl ? 'No product page link' : '')}
                      style={canOpenProductPage ? { cursor: 'pointer' } : {}}
                    >
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
                    <div
                      className="product-info-wrapper"
                      onClick={openProductPage}
                      role={canOpenProductPage ? 'button' : undefined}
                      title={canOpenProductPage ? 'View product on brand site' : ''}
                      style={canOpenProductPage ? { cursor: 'pointer' } : {}}
                    >
                      <div className="product-name-small">{product.name}</div>
                      <div className="product-brand-small">{product.brand || 'N/A'}</div>
                      <div className="product-meta">
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

