import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';
import './App.css';

// Import components
import LandingPage from './components/LandingPage';
import Pricing from './components/Pricing';
import PaymentSuccess from './pages/PaymentSuccess';
import PaymentCancel from './pages/PaymentCancel';
import Dashboard from './components/Dashboard';
import PropertyCreator from './components/PropertyCreator';
import ViralContentGenerator from './components/ViralContentGenerator';
import Analytics from './components/Analytics';
import VirtualTourUploadPage from './components/VirtualTourUploadPage';
import VirtualTourViewer from './components/VirtualTourViewer';
import TermsAndConditions from './components/TermsAndConditions';
import PrivacyPolicy from './components/PrivacyPolicy';

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// const API = `${BACKEND_URL}/api`;

// User Context
const UserContext = React.createContext();

// Protected Route Component
function ProtectedRoute({ children }) {
  const { user } = React.useContext(UserContext);
  
  if (!user) {
    toast.error('Please log in to access this page');
    return <Navigate to="/" />;
  }
  
  if (!user.subscription || !user.subscription.active) {
    toast.error('Please select a subscription plan to continue');
    return <Navigate to="/pricing" />;
  }
  
  return children;
}

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing user session
    const savedUser = localStorage.getItem('listingspark_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        localStorage.removeItem('listingspark_user');
      }
    }
    setLoading(false);
  }, []);

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('listingspark_user', JSON.stringify(userData));
    toast.success(`Welcome, ${userData.name}!`);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('listingspark_user');
    toast.success('Logged out successfully');
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
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-white border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <UserContext.Provider value={{ user, login, logout, updateUserSubscription }}>
      <BrowserRouter>
        <div className="App">
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/payment/success" element={<PaymentSuccess />} />
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
      </BrowserRouter>
    </UserContext.Provider>
  );
}

export { UserContext };
export default App;
