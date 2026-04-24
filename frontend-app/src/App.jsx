import { useState } from 'react'
import axios from 'axios'
import { useAuth } from './context/AuthContext'
import { getApiOrigin } from './lib/apiOrigin'

const API_BASE_URL = getApiOrigin()

function App() {
  const { user } = useAuth()
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [failedImages, setFailedImages] = useState(new Set()) // Track products with failed image loads

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      processFile(file)
    }
  }

  // Process selected file
  const processFile = (file) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file (JPG, PNG, WebP, BMP)')
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image size must be less than 10MB')
      return
    }

    setSelectedFile(file)
    setError(null)
    setResults(null)

    // Create preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setPreviewUrl(reader.result)
    }
    reader.readAsDataURL(file)
  }

  // Handle drag and drop
  const handleDragOver = (event) => {
    event.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = (event) => {
    event.preventDefault()
    setDragging(false)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    
    const file = event.dataTransfer.files[0]
    if (file) {
      processFile(file)
    }
  }

  // Handle search
  const handleSearch = async () => {
    if (!user) {
      setError('Please login to use the search feature')
      return
    }

    if (!selectedFile) {
      setError('Please select an image first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await axios.post(
        `${API_BASE_URL}/api/search/upload?top_k=5`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      setResults(response.data)
    } catch (err) {
      console.error('Search error:', err)
      setError(err.response?.data?.detail || 'Failed to search. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  // Reset
  const handleReset = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
    setResults(null)
    setError(null)
  }

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <h1>DupeFinder</h1>
        <p>Find Affordable Alternatives to Luxury Fashion</p>
      </div>

      <div className="container">
        {/* Upload Section */}
        <div className="upload-section">
          <div
            className={`upload-area ${dragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('fileInput').click()}
          >
            <div className="upload-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
            </div>
            <h2>Upload Your Fashion Image</h2>
            <p>Drag and drop or click to browse</p>
            <p style={{ fontSize: '0.9rem', color: '#999' }}>
              Supports: JPG, PNG, WebP, BMP (Max 10MB)
            </p>
            <input
              id="fileInput"
              type="file"
              className="file-input"
              accept="image/*"
              onChange={handleFileSelect}
            />
          </div>

          {/* Preview */}
          {previewUrl && (
            <div className="preview-section">
              <img src={previewUrl} alt="Preview" className="preview-image" />
              <div style={{ marginTop: '20px' }}>
                <button 
                  className="upload-button" 
                  onClick={handleSearch} 
                  disabled={loading || !user}
                  title={!user ? 'Please login to search' : ''}
                >
                  {loading ? 'Searching...' : 'Find Similar Products'}
                </button>
                <button 
                  className="upload-button" 
                  onClick={handleReset}
                  style={{ marginLeft: '10px', background: '#6c757d' }}
                >
                  Try Another Image
                </button>
              </div>
              {!user && (
                <div style={{ marginTop: '15px', padding: '15px', background: '#fff3cd', borderRadius: '8px', color: '#856404' }}>
                  Please login to use the search feature
                </div>
              )}
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Analyzing your image with AI...</p>
            <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>
              Extracting features using ResNet50 neural network
            </p>
          </div>
        )}

        {/* Results */}
        {results && results.results && results.results.length > 0 && (
          <div className="results-section">
            <div className="results-header">
              <h2>Similar Products Found</h2>
              <div className="search-stats">
                Found {results.total_results} similar products in {results.search_time_ms.toFixed(2)}ms
              </div>
            </div>

            <div className="results-grid">
              {results.results
                .filter(product => {
                  const productId = product.product_id || product._id || product.name
                  return !failedImages.has(productId)
                })
                .map((product, index) => (
                <div key={product._id} className="product-card">
                  <img 
                    src={`${API_BASE_URL}/data/${product.image_path.replace(/\\/g, '/')}`}
                    alt={product.name}
                    className="product-image"
                    onError={(e) => {
                      // If image fails to load, hide the product from display
                      const productId = product.product_id || product._id || product.name
                      setFailedImages(prev => new Set([...prev, productId]))
                      // Hide the product card immediately
                      if (e.target.closest('.product-card')) {
                        e.target.closest('.product-card').style.display = 'none'
                      }
                    }}
                  />
                  <div className="product-info">
                    <div className="product-name">{product.name}</div>
                    <span className="product-category">{product.category}</span>
                    <div className="product-details">
                      <span className="product-brand">{product.brand}</span>
                      <span className="product-price">PKR {parseFloat(product.price).toFixed(2)}</span>
                    </div>
                    <div className="similarity-badge">
                      {(product.similarity_score * 100).toFixed(1)}% Match
                    </div>
                    {index === 0 && (
                      <div style={{ marginTop: '10px', color: '#667eea', fontWeight: '600' }}>
                        Best Match
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !results && !previewUrl && (
          <div className="empty-state">
            <h3>Welcome to DupeFinder</h3>
            <p>Upload a fashion image to find affordable alternatives</p>
            <p style={{ marginTop: '20px', fontSize: '1rem', color: '#667eea' }}>
              Bags • Shoes • Watches • Clothing • Accessories
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App

