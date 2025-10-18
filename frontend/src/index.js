import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// 🔍 Global error & promise rejection handlers
window.addEventListener('error', function (event) {
  console.error('🔥 Global Error Caught:', event.message, 'at', event.filename, ':', event.lineno);
});

window.addEventListener('unhandledrejection', function (event) {
  console.error('💥 Unhandled Promise Rejection:', event.reason);
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
