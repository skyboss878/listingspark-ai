import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api' || 'http://localhost:8000/api';

const Analytics = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, [propertyId]);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/properties/${propertyId}/analytics`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="spinner mb-4"></div>
          <p>Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-2xl hover:text-purple-300 transition-colors"
          >
            ←
          </button>
          <h1 className="text-3xl font-bold">Property Analytics</h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="glass rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">👀</span>
              <div className="text-2xl font-bold text-blue-400">
                {analytics?.views || 0}
              </div>
            </div>
            <p className="text-sm opacity-80">Total Views</p>
          </motion.div>

          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">📤</span>
              <div className="text-2xl font-bold text-green-400">
                {analytics?.shares || 0}
              </div>
            </div>
            <p className="text-sm opacity-80">Total Shares</p>
          </motion.div>

          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="glass rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">⚡</span>
              <div className="text-2xl font-bold text-purple-400">
                {Math.round((analytics?.engagement_rate || 0) * 100)}%
              </div>
            </div>
            <p className="text-sm opacity-80">Engagement Rate</p>
          </motion.div>

          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-2xl">🔥</span>
              <div className="text-2xl font-bold text-red-400">
                {analytics?.viral_score || 0}
              </div>
            </div>
            <p className="text-sm opacity-80">Viral Score</p>
          </motion.div>
        </div>

        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="glass rounded-xl p-8 text-center"
        >
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-xl font-semibold mb-2">Detailed Analytics Coming Soon</h3>
          <p className="opacity-80">Advanced analytics dashboard with platform-specific metrics, trending analysis, and performance insights.</p>
        </motion.div>
      </div>
    </div>
  );
};

export default Analytics;
