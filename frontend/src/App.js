import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';
import axios from 'axios';
import './App.css';

// Import components
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import PropertyCreator from './components/PropertyCreator';
import ViralContentGenerator from './components/ViralContentGenerator';
import Analytics from './components/Analytics';
import VirtualTourUploadPage from './components/VirtualTourUploadPage';
import VirtualTourViewer from './components/VirtualTourViewer';
import TermsAndConditions from './components/TermsAndConditions';
import PrivacyPolicy from './components/PrivacyPolicy';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

// User Context
const UserContext = React.createContext();

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
    toast.success(`Welcome back, ${userData.name}!`);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('listingspark_user');
    toast.success('Logged out successfully');
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
    <UserContext.Provider value={{ user, login, logout }}>
      <BrowserRouter>
        <div className="App">
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/terms" element={<TermsAndConditions />} />
              <Route path="/privacy" element={<PrivacyPolicy />} />
              <Route 
                path="/dashboard" 
                element={user ? <Dashboard /> : <Navigate to="/" />} 
              />
              <Route 
                path="/create-property" 
                element={user ? <PropertyCreator /> : <Navigate to="/" />} 
              />
              <Route 
                path="/viral-content/:propertyId" 
                element={user ? <ViralContentGenerator /> : <Navigate to="/" />} 
              />
              <Route 
                path="/analytics/:propertyId" 
                element={user ? <Analytics /> : <Navigate to="/" />} 
              />
              <Route 
                path="/upload-tour/:propertyId" 
                element={user ? <VirtualTourUploadPage /> : <Navigate to="/" />} 
              />
              <Route 
                path="/virtual-tour/:propertyId" 
                element={user ? <VirtualTourViewer /> : <Navigate to="/" />} 
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
