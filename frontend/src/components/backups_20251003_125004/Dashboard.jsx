import React, { useState, useEffect, useContext } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import toast from 'react-hot-toast';
import axios from 'axios';
import { UserContext } from '../App';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const Dashboard = () => {
  const { user, logout } = useContext(UserContext);
  const [dashboardData, setDashboardData] = useState(null);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard stats
      const dashboardResponse = await axios.get(`${API_URL}/api/dashboard/${user.id}`);
      setDashboardData(dashboardResponse.data);
      
      // Load user properties
      const propertiesResponse = await axios.get(`${API_URL}/api/properties/${user.id}`);
      setProperties(propertiesResponse.data);
      
    } catch (error) {
      console.error('Error loading dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: 'Create New Property',
      description: 'Add a new property listing to your portfolio',
      icon: '🏠',
      action: () => navigate('/create-property'),
      gradient: 'from-blue-500 to-blue-600'
    },
    {
      title: 'Generate Viral Content',
      description: 'Create engaging social media content for your listings',
      icon: '🚀',
      action: () => properties.length > 0 ? navigate(`/viral-content/${properties[0].id}`) : toast.error('Create a property first'),
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      title: 'View Analytics',
      description: 'Track performance and engagement metrics',
      icon: '📊',
      action: () => properties.length > 0 ? navigate(`/analytics/${properties[0].id}`) : toast.error('Create a property first'),
      gradient: 'from-green-500 to-teal-500'
    }
  ];

  const getPlanFeatures = (plan) => {
    const features = {
      starter: { maxProperties: 5, contentGenerations: 50, analytics: 'Basic' },
      professional: { maxProperties: 'Unlimited', contentGenerations: 500, analytics: 'Advanced' },
      enterprise: { maxProperties: 'Unlimited', contentGenerations: 'Unlimited', analytics: 'Premium' }
    };
    return features[plan] || features.starter;
  };

  const planLimits = getPlanFeatures(user?.plan || 'starter');

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <span className="text-2xl">⚡</span>
              <div>
                <h1 className="text-xl font-bold text-gray-900">ListingSpark AI</h1>
                <p className="text-sm text-gray-500">Welcome back, {user?.name}!</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900 capitalize">{user?.plan} Plan</div>
                <div className="text-xs text-gray-500">14 days trial remaining</div>
              </div>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Properties</p>
                <p className="text-3xl font-bold text-gray-900">
                  {properties.length}
                  <span className="text-sm text-gray-500 ml-2">/ {planLimits.maxProperties}</span>
                </p>
              </div>
              <div className="text-3xl">🏠</div>
            </div>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Views</p>
                <p className="text-3xl font-bold text-gray-900">
                  {dashboardData?.stats?.total_views || 0}
                </p>
              </div>
              <div className="text-3xl">👀</div>
            </div>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Shares</p>
                <p className="text-3xl font-bold text-gray-900">
                  {dashboardData?.stats?.total_shares || 0}
                </p>
              </div>
              <div className="text-3xl">🔄</div>
            </div>
          </motion.div>

          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Viral Score</p>
                <p className="text-3xl font-bold text-gradient bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  {Math.round(dashboardData?.stats?.average_viral_score || 0)}
                </p>
              </div>
              <div className="text-3xl">🚀</div>
            </div>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {quickActions.map((action, index) => (
              <motion.button
                key={index}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={action.action}
                className={`bg-gradient-to-r ${action.gradient} text-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all text-left`}
              >
                <div className="text-4xl mb-3">{action.icon}</div>
                <h3 className="text-xl font-bold mb-2">{action.title}</h3>
                <p className="text-white/90 text-sm">{action.description}</p>
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Recent Properties & Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
{/* Recent Properties */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-4">Recent Properties</h3>
            <div className="space-y-4">
              {properties.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-6xl mb-4">🏠</div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No properties yet</h4>
                  <p className="text-gray-500 mb-4">Create your first property listing to get started!</p>
                  <button
                    onClick={() => navigate('/create-property')}
                    className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    Create Property
                  </button>
                </div>
              ) : (
                properties.slice(0, 5).map((property) => (
                  <div key={property.id} className="flex items-center justify-between p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold">
                        {property.title.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">{property.title}</h4>
                        <p className="text-sm text-gray-500">{property.address}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900">{property.price}</div>
                      <div className="text-sm text-gray-500">{property.property_type}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>

          {/* Performance Chart */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-4">Performance Overview</h3>
            {properties.length > 0 ? (
              <div className="space-y-6">
                {/* Engagement Chart */}
                <div>
                  <Bar
                    data={{
                      labels: properties.slice(0, 5).map(p => p.title.length > 15 ? p.title.substring(0, 15) + '...' : p.title),
                      datasets: [
                        {
                          label: 'Views',
                          data: properties.slice(0, 5).map(() => Math.floor(Math.random() * 1000) + 100),
                          backgroundColor: 'rgba(147, 51, 234, 0.1)',
                          borderColor: 'rgb(147, 51, 234)',
                          borderWidth: 2,
                        },
                        {
                          label: 'Shares',
                          data: properties.slice(0, 5).map(() => Math.floor(Math.random() * 200) + 20),
                          backgroundColor: 'rgba(236, 72, 153, 0.1)',
                          borderColor: 'rgb(236, 72, 153)',
                          borderWidth: 2,
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                        title: {
                          display: true,
                          text: 'Property Engagement'
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true
                        }
                      }
                    }}
                  />
                </div>

                {/* Platform Performance */}
                <div className="pt-4 border-t border-gray-100">
                  <h4 className="font-medium text-gray-900 mb-3">Platform Performance</h4>
                  <Doughnut
                    data={{
                      labels: ['Instagram', 'TikTok', 'Facebook', 'Twitter'],
                      datasets: [{
                        data: [35, 30, 20, 15],
                        backgroundColor: [
                          '#E4405F',
                          '#000000',
                          '#1877F2',
                          '#1DA1F2'
                        ],
                        borderWidth: 0
                      }]
                    }}
                    options={{
                      responsive: true,
                      plugins: {
                        legend: {
                          position: 'bottom'
                        }
                      }
                    }}
                  />
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">📊</div>
                <p className="text-gray-500">Create properties to see performance data</p>
              </div>
            )}
          </motion.div>
        </div>

        {/* Plan Usage */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="mt-8 bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-900">Plan Usage</h3>
            <button
              onClick={() => navigate('/#pricing')}
              className="text-purple-600 hover:text-purple-700 font-medium transition-colors"
            >
              Upgrade Plan
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Properties Usage */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Properties</span>
                <span className="text-sm font-medium text-gray-900">
                  {properties.length} / {planLimits.maxProperties}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: planLimits.maxProperties === 'Unlimited' 
                      ? '20%' 
                      : `${(properties.length / planLimits.maxProperties) * 100}%`
                  }}
                />
              </div>
            </div>

            {/* Content Generations */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Content Generations</span>
                <span className="text-sm font-medium text-gray-900">
                  {Math.floor(Math.random() * 50)} / {planLimits.contentGenerations}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: '15%' }}
                />
              </div>
            </div>

            {/* Analytics Level */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Analytics</span>
                <span className="text-sm font-medium text-gray-900">{planLimits.analytics}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  planLimits.analytics === 'Premium' ? 'bg-yellow-500' :
                  planLimits.analytics === 'Advanced' ? 'bg-blue-500' : 'bg-gray-400'
                }`} />
                <span className="text-sm text-gray-600">
                  {planLimits.analytics === 'Premium' ? 'All features unlocked' :
                   planLimits.analytics === 'Advanced' ? 'Most features available' : 'Basic tracking only'}
                </span>
              </div>
            </div>
          </div>

          {user?.plan === 'starter' && (
            <div className="mt-6 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">🚀</div>
                <div>
                  <h4 className="font-medium text-purple-900">Ready to go viral?</h4>
                  <p className="text-purple-700 text-sm">Upgrade to Professional for unlimited properties and advanced AI features.</p>
                </div>
                <button
                  onClick={() => navigate('/#pricing')}
                  className="ml-auto bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
                >
                  Upgrade Now
                </button>
              </div>
            </div>
          )}
        </motion.div>

        {/* Recent Activity */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-8 bg-white rounded-xl p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {[
              { action: 'Property created', item: 'Luxury Downtown Condo', time: '2 hours ago', icon: '🏠' },
              { action: 'Viral content generated', item: 'Instagram post for Modern Villa', time: '5 hours ago', icon: '📱' },
              { action: 'Analytics updated', item: 'Suburban Family Home', time: '1 day ago', icon: '📊' },
              { action: 'Content shared', item: 'TikTok video went viral', time: '2 days ago', icon: '🚀' }
            ].map((activity, index) => (
              <div key={index} className="flex items-center space-x-4 p-3 hover:bg-gray-50 rounded-lg transition-colors">
                <div className="text-2xl">{activity.icon}</div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                  <p className="text-sm text-gray-500">{activity.item}</p>
                </div>
                <div className="text-xs text-gray-400">{activity.time}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
