/**
 * DupeFinder Admin Dashboard - Main App Component
 */

import React from 'react';

function App() {
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1>DupeFinder Admin Dashboard</h1>
        <p>Manage products, reviews, and analytics</p>
        <p style={styles.status}>⚠️ Dashboard is under development</p>
      </header>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    padding: '20px',
  },
  header: {
    maxWidth: '800px',
  },
  status: {
    marginTop: '20px',
    padding: '10px 20px',
    background: 'rgba(255, 255, 255, 0.2)',
    borderRadius: '5px',
    display: 'inline-block',
  },
};

export default App;

