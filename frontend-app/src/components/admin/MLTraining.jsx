import { useState, useEffect } from 'react'
import axios from 'axios'

function MLTraining() {
  const [trainSplit, setTrainSplit] = useState(80)
  const [training, setTraining] = useState(false)
  const [currentJob, setCurrentJob] = useState(null)
  const [metrics, setMetrics] = useState([])
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    fetchMetrics()
  }, [])

  useEffect(() => {
    if (currentJob && training) {
      const interval = setInterval(() => {
        checkTrainingStatus()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [currentJob, training])

  const fetchMetrics = async () => {
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const response = await axios.get(
        'http://localhost:8000/api/admin/ml/metrics?limit=10',
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setMetrics(response.data.metrics)
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    }
  }

  const showNotification = (message, type) => {
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

  const startTraining = async () => {
    // Deactivated - show coming soon notification
    showNotification('ML Training feature coming soon!', 'error')
    return
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const response = await axios.post(
        `http://localhost:8000/api/admin/ml/train?train_split=${trainSplit / 100}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setCurrentJob(response.data.job_id)
      setTraining(true)
      setProgress(0)
    } catch (error) {
      console.error('Failed to start training:', error)
      alert('Failed to start training: ' + (error.response?.data?.detail || error.message))
    }
  }

  const checkTrainingStatus = async () => {
    try {
      const token = localStorage.getItem('adminToken') || localStorage.getItem('token')
      const response = await axios.get(
        `http://localhost:8000/api/admin/ml/training-status/${currentJob}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setProgress(response.data.progress)

      if (response.data.status === 'completed') {
        setTraining(false)
        alert('Training completed successfully!')
        fetchMetrics()
      } else if (response.data.status === 'failed') {
        setTraining(false)
        alert('Training failed: ' + response.data.error)
      }
    } catch (error) {
      console.error('Failed to check status:', error)
    }
  }

  return (
    <div className="ml-training">
      <div className="module-header">
        <h2>ML Model Training Dashboard</h2>
        <p>Train the similarity model with custom parameters</p>
      </div>

      {/* Training Controls */}
      <div className="section-card">
        <h3>Training Configuration</h3>
        
        <div className="slider-section">
          <label className="slider-label">
            Train/Test Split: <strong>{trainSplit}%</strong> train / <strong>{100 - trainSplit}%</strong> test
          </label>
          <input
            type="range"
            min="50"
            max="95"
            value={trainSplit}
            onChange={(e) => setTrainSplit(parseInt(e.target.value))}
            className="slider"
            disabled={training}
          />
          <div className="slider-marks">
            <span>50%</span>
            <span>60%</span>
            <span>70%</span>
            <span>80%</span>
            <span>90%</span>
            <span>95%</span>
          </div>
        </div>

        <button
          onClick={startTraining}
          className="train-btn"
          style={{ opacity: 0.6, cursor: 'not-allowed' }}
        >
          Start Training
        </button>

        {training && (
          <div className="progress-section">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="progress-text">{progress}% Complete</p>
          </div>
        )}
      </div>

      {/* Metrics Display */}
      <div className="section-card">
        <h3>Training History & Metrics</h3>
        
        {metrics.length === 0 ? (
          <p>No training history yet. Start your first training!</p>
        ) : (
          <div className="metrics-grid">
            {metrics.map((job, idx) => (
              <div key={job.job_id || idx} className="metric-card">
                <div className="metric-header">
                  <span className="metric-date">
                    {new Date(job.completed_at).toLocaleString()}
                  </span>
                  <span className="metric-split">
                    Split: {(job.train_split * 100).toFixed(0)}%
                  </span>
                </div>
                
                {job.metrics && (
                  <div className="metric-values">
                    <div className="metric-item">
                      <span className="metric-label">Accuracy</span>
                      <span className="metric-value">
                        {(job.metrics.accuracy * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-label">Precision</span>
                      <span className="metric-value">
                        {(job.metrics.precision * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-label">Recall</span>
                      <span className="metric-value">
                        {(job.metrics.recall * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-label">F1 Score</span>
                      <span className="metric-value">
                        {(job.metrics.f1_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Current Best Model */}
      {metrics.length > 0 && metrics[0].metrics && (
        <div className="section-card best-model">
          <h3>Current Best Model</h3>
          <div className="best-model-stats">
            <div className="stat-box">
              <div className="stat-value">{(metrics[0].metrics.accuracy * 100).toFixed(1)}%</div>
              <div className="stat-label">Accuracy</div>
            </div>
            <div className="stat-box">
              <div className="stat-value">{(metrics[0].metrics.precision * 100).toFixed(1)}%</div>
              <div className="stat-label">Precision</div>
            </div>
            <div className="stat-box">
              <div className="stat-value">{(metrics[0].metrics.recall * 100).toFixed(1)}%</div>
              <div className="stat-label">Recall</div>
            </div>
            <div className="stat-box">
              <div className="stat-value">{(metrics[0].metrics.f1_score * 100).toFixed(1)}%</div>
              <div className="stat-label">F1 Score</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MLTraining

