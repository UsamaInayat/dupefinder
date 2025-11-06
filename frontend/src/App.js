/**
 * DupeFinder - Main App Component
 */

import React from 'react';
import './styles/App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>DupeFinder</h1>
        <p>Find Affordable Alternatives to Luxury Fashion</p>
        <p className="status">⚠️ Application is under development</p>
      </header>
      
      <main>
        <section className="hero">
          <h2>Welcome to DupeFinder</h2>
          <p>Upload an image of any luxury item and discover affordable alternatives</p>
        </section>
        
        <section className="features">
          <div className="feature">
            <h3>📸 Image Search</h3>
            <p>Upload or capture photos of luxury items</p>
          </div>
          <div className="feature">
            <h3>🔍 Smart Matching</h3>
            <p>AI-powered visual similarity search</p>
          </div>
          <div className="feature">
            <h3>💰 Save Money</h3>
            <p>Compare prices and track your savings</p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;

