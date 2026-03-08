import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from '@/contexts/AuthContext';
import App from './App';
import './index.css';

class AppErrorBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24, fontFamily: 'system-ui', maxWidth: 600 }}>
          <h1 style={{ color: '#c53030', marginBottom: 8 }}>Something went wrong</h1>
          <pre style={{ background: '#1a1a1a', color: '#e2e8f0', padding: 16, borderRadius: 8, overflow: 'auto' }}>
            {this.state.error?.message ?? String(this.state.error)}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <App />
          <Toaster
        position="top-center"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'var(--color-bg-elevated)',
            color: 'var(--color-text-primary)',
            border: '1px solid var(--color-border)',
            borderRadius: '12px',
            fontSize: '14px',
            fontFamily: 'var(--font-sans)',
          },
        }}
      />
      </BrowserRouter>
    </AuthProvider>
    </AppErrorBoundary>
  </React.StrictMode>,
);
