import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';
import './App.css';

// Import components
import LandingPage from './components/LandingPage';
import Login from './components/Login';
import Pricing from './components/Pricing';
import PaymentCancel from './pages/PaymentCancel';
import Dashboard from './components/Dashboard';
import CreateListing from './components/CreateListing';
import MLSSetup from './components/MLSSetup';
import PropertyCreator from './components/PropertyCreator';
import ViralContentGenerator from './components/ViralContentGenerator';
import Analytics from './components/Analytics';
import VirtualTourUploadPage from './components/VirtualTourUploadPage';
import VirtualTourViewer from './components/VirtualTourViewer';
import TermsAndConditions from './components/TermsAndConditions';
import PrivacyPolicy from './components/PrivacyPolicy';
import ProCamera360 from './components/ProCamera360';

// Create User Context
export const UserContext = React.createContext();

// Protected Route Component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token') || localStorage.getItem('auth_token');

  if (!token) {
    toast.error('Please log in to access this page');
    return <Navigate to="/login" replace />;
  }

  return children;
}

// Inner App component that uses navigation hooks
function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Load user session
  useEffect(() => {
    const savedUser = localStorage.getItem('listingspark_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Error parsing saved user:', error);
        localStorage.removeItem('listingspark_user');
      }
    }
    setLoading(false);
  }, []);

  // PayPal return handling
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('paypal_success') === 'true') {
      const token = localStorage.getItem('listingspark_user');
      if (!token) {
        toast.error('Session expired during payment. Please login again.');
        navigate('/login');
      } else {
        toast.success('Payment successful! 🎉');
      }

      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, [navigate]);

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('listingspark_user', JSON.stringify(userData));
    toast.success(`Welcome, ${userData.full_name || userData.name || 'Agent'}!`);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('listingspark_user');
    localStorage.removeItem('token');
    localStorage.removeItem('auth_token');
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const updateUserSubscription = (subscriptionData) => {
    const updatedUser = { ...user, subscription: subscriptionData };
    setUser(updatedUser);
    localStorage.setItem('listingspark_user', JSON.stringify(updatedUser));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-4 border-white border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <UserContext.Provider value={{ user, login, logout, updateUserSubscription }}>
      <div className="App">
        <AnimatePresence mode="wait">
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/payment/cancel" element={<PaymentCancel />} />
            <Route path="/terms" element={<TermsAndConditions />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />

            {/* Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/create-listing"
              element={
                <ProtectedRoute>
                  <CreateListing />
                </ProtectedRoute>
              }
            />
            <Route
              path="/mls-setup"
              element={
                <ProtectedRoute>
                  <MLSSetup />
                </ProtectedRoute>
              }
            />
            <Route
              path="/create-property"
              element={
                <ProtectedRoute>
                  <PropertyCreator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/viral-content/:propertyId"
              element={
                <ProtectedRoute>
                  <ViralContentGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics/:propertyId"
              element={
                <ProtectedRoute>
                  <Analytics />
                </ProtectedRoute>
              }
            />
            <Route
              path="/upload-tour/:propertyId"
              element={
                <ProtectedRoute>
                  <VirtualTourUploadPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/virtual-tour/:propertyId"
              element={
                <ProtectedRoute>
                  <VirtualTourViewer />
                </ProtectedRoute>
              }
            />

            {/* Catch all - redirect to landing page */}
            <Route path="*" element={<Navigate to="/" replace />} />
        <Route path="/camera360" element={<ProtectedRoute><ProCamera360 onCapture={(file) => console.log("Captured:", file)} onClose={() => window.history.back()} propertyType="luxury" /></ProtectedRoute>} />
          </Routes>
        </AnimatePresence>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1f2937',
              color: '#ffffff',
              border: '1px solid #374151',
            },
          }}
        />
      </div>
    </UserContext.Provider>
  );
}

// Main App component with BrowserRouter wrapper
function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
