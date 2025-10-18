import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../utils/api';
import toast from 'react-hot-toast';

const Analytics = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.analytics.get(propertyId);
      setAnalytics(data);
    } catch (error) {
      console.error('Error loading analytics:', error);
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [propertyId]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p>Loading analytics...</p>
        </div>
      </div>
    );
  }

  const getTrendingColor = (status) => {
    switch (status) {
      case 'viral': return 'from-red-500 to-pink-500';
      case 'trending': return 'from-orange-500 to-yellow-500';
      case 'growing': return 'from-green-500 to-blue-500';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const getTrendingIcon = (status) => {
    switch (status) {
      case 'viral': return '🔥';
      case 'trending': return '📈';
      case 'growing': return '🌱';
      default: return '📊';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white py-12">
      <div className="container mx-auto px-6 max-w-6xl">
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <button
            onClick={() => navigate('/dashboard')}
            className="text-purple-200 hover:text-white mb-4 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-bold mb-2">Property Analytics</h1>
          <p className="text-purple-200">Track your property's performance</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">👀</span>
              <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">
                {analytics.views}
              </div>
            </div>
            <p className="text-sm opacity-80">Total Views</p>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="glass rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">🔄</span>
              <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-purple-600">
                {analytics.tour_views}
              </div>
            </div>
            <p className="text-sm opacity-80">Tour Views</p>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">📤</span>
              <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-pink-600">
                {analytics.shares}
              </div>
            </div>
            <p className="text-sm opacity-80">Total Shares</p>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="glass rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">⚡</span>
              <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-green-600">
                {analytics.engagement_rate.toFixed(1)}%
              </div>
            </div>
            <p className="text-sm opacity-80">Engagement Rate</p>
          </motion.div>
        </div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
        >
          <div className="glass rounded-xl p-8">
            <h2 className="text-2xl font-bold mb-6">Viral Score</h2>
            <div className="flex items-center justify-center mb-6">
              <div className="relative">
                <svg className="w-48 h-48 transform -rotate-90">
                  <circle
                    cx="96"
                    cy="96"
                    r="80"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="12"
                    fill="none"
                  />
                  <circle
                    cx="96"
                    cy="96"
                    r="80"
                    stroke="url(#gradient)"
                    strokeWidth="12"
                    fill="none"
                    strokeDasharray={`${(analytics.viral_score / 100) * 502.4} 502.4`}
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#10b981" />
                      <stop offset="50%" stopColor="#3b82f6" />
                      <stop offset="100%" stopColor="#8b5cf6" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-5xl font-bold">{analytics.viral_score}</div>
                    <div className="text-sm text-purple-200">/ 100</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="text-center">
              <p className="text-purple-200 mb-2">
                Your property is performing{' '}
                {analytics.viral_score >= 80 ? 'excellently' :
                 analytics.viral_score >= 60 ? 'well' :
                 analytics.viral_score >= 40 ? 'moderately' : 'okay'}
              </p>
            </div>
          </div>

          <div className="glass rounded-xl p-8">
            <h2 className="text-2xl font-bold mb-6">Trending Status</h2>
            <div className="flex items-center justify-center mb-6">
              <div className={`text-8xl bg-gradient-to-r ${getTrendingColor(analytics.trending_status)} bg-clip-text text-transparent`}>
                {getTrendingIcon(analytics.trending_status)}
              </div>
            </div>
            <div className="text-center">
              <h3 className="text-2xl font-bold mb-2 capitalize">
                {analytics.trending_status}
              </h3>
              <p className="text-purple-200">
                {analytics.trending_status === 'viral' && 'Your property is going viral! 🎉'}
                {analytics.trending_status === 'trending' && 'Great momentum! Keep it up!'}
                {analytics.trending_status === 'growing' && 'Steady growth, looking good!'}
                {analytics.trending_status === 'normal' && 'Standard performance'}
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="glass rounded-xl p-8 mt-8"
        >
          <h2 className="text-2xl font-bold mb-6">Performance Insights</h2>
          <div className="space-y-4">
            {analytics.tour_views > 0 && (
              <div className="flex items-start gap-3 p-4 bg-purple-500/20 rounded-lg">
                <span className="text-2xl">🔄</span>
                <div>
                  <h4 className="font-semibold mb-1">Virtual Tour Impact</h4>
                  <p className="text-sm text-purple-200">
                    Your 360° tour has been viewed {analytics.tour_views} times! Properties with tours get{' '}
                    {((analytics.tour_views / analytics.views) * 100).toFixed(0)}% more engagement.
                  </p>
                </div>
              </div>
            )}

            {analytics.engagement_rate > 5 && (
              <div className="flex items-start gap-3 p-4 bg-green-500/20 rounded-lg">
                <span className="text-2xl">⚡</span>
                <div>
                  <h4 className="font-semibold mb-1">High Engagement</h4>
                  <p className="text-sm text-purple-200">
                    Your engagement rate of {analytics.engagement_rate.toFixed(1)}% is above average! Keep creating great content.
                  </p>
                </div>
              </div>
            )}

            {analytics.viral_score >= 70 && (
              <div className="flex items-start gap-3 p-4 bg-orange-500/20 rounded-lg">
                <span className="text-2xl">🔥</span>
                <div>
                  <h4 className="font-semibold mb-1">Viral Potential</h4>
                  <p className="text-sm text-purple-200">
                    Your content has high viral potential! Share it across more platforms for maximum reach.
                  </p>
                </div>
              </div>
            )}

            {analytics.views === 0 && (
              <div className="flex items-start gap-3 p-4 bg-blue-500/20 rounded-lg">
                <span className="text-2xl">💡</span>
                <div>
                  <h4 className="font-semibold mb-1">Getting Started</h4>
                  <p className="text-sm text-purple-200">
                    Start sharing your viral content to get your first views! Add a 360° tour to boost engagement.
                  </p>
                </div>
              </div>
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="mt-8 flex gap-4"
        >
          <button
            onClick={() => navigate(`/viral-content/${propertyId}`)}
            className="flex-1 btn-viral py-4"
          >
            View Viral Content
          </button>
          <button
            onClick={() => navigate(`/virtual-tour/${propertyId}`)}
            className="flex-1 px-6 py-4 border border-white/30 rounded-lg hover:bg-white/10 transition-all"
          >
            View Virtual Tour
          </button>
        </motion.div>
      </div>
    </div>
  );
};

export default Analytics;
