import React from 'react';

const App: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <header style={{ marginBottom: '20px' }}>
        <h1 style={{ color: '#333' }}>🛡️ GuardNet Security Dashboard</h1>
        <p style={{ color: '#666' }}>DNS Filtering & Security Monitoring</p>
      </header>
      
      <main>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '20px' 
        }}>
          <div style={{ 
            padding: '20px', 
            border: '1px solid #ddd', 
            borderRadius: '8px',
            backgroundColor: '#f9f9f9'
          }}>
            <h3>🌐 DNS Filtering Status</h3>
            <p>Service Status: <span style={{ color: 'green' }}>Active</span></p>
            <p>Blocked Requests Today: 1,234</p>
          </div>
          
          <div style={{ 
            padding: '20px', 
            border: '1px solid #ddd', 
            borderRadius: '8px',
            backgroundColor: '#f9f9f9'
          }}>
            <h3>📊 Security Metrics</h3>
            <p>Threats Blocked: 567</p>
            <p>Clean Requests: 12,890</p>
          </div>
          
          <div style={{ 
            padding: '20px', 
            border: '1px solid #ddd', 
            borderRadius: '8px',
            backgroundColor: '#f9f9f9'
          }}>
            <h3>⚙️ System Health</h3>
            <p>API Gateway: <span style={{ color: 'green' }}>Online</span></p>
            <p>Database: <span style={{ color: 'green' }}>Connected</span></p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;