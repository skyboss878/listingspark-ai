import React, { useState, useEffect, useContext, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { UserContext } from '../App';
import axios from 'axios';
import toast from 'react-hot-toast';

const API = process.env.REACT_APP_BACKEND_URL + '/api' || 'http://localhost:8000/api';

const Dashboard = () => {
  const { user, logout } = useContext(UserContext);
  const navigate = useNavigate();
  const [properties, setProperties] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [propertiesRes, dashboardRes] = await Promise.all([
        axios.get(`${API}/properties/${user.id}`),
        axios.get(`${API}/dashboard/${user.id}`)
      ]);

      setProperties(propertiesRes.data);
      setStats(dashboardRes.data.stats);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [user]);

  const generateViralContent = async (propertyId) => {
    try {
      toast.loading('Generating viral content...', { id: 'viral-gen' });

      await axios.post(`${API}/properties/${propertyId}/viral-content`);

      toast.success('Viral content generated!', { id: 'viral-gen' });
      navigate(`/viral-content/${propertyId}`);
    } catch (error) {
      toast.error('Failed to generate content', { id: 'viral-gen' });
    }
  };

  const viewTour = (propertyId) => {
    navigate(`/virtual-tour/${propertyId}`);
  };


  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="spinner mb-4"></div>
          <p>Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <motion.h1 
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              className="text-3xl font-bold mb-2"
            >
              Welcome back, {user?.name}! 👋
            </motion.h1>
            <p className="text-purple-200">Ready to create more viral content with 360° tours?</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => navigate('/create-property')}
              className="btn-viral"
            >
              + New Property
            </button>
            <button
              onClick={logout}
              className="border border-white/30 rounded-lg px-4 py-2 hover:bg-white/10 transition-all"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Enhanced Stats Grid with Tour Stats */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8"
        >
          {[
            { 
              label: 'Total Properties', 
              value: stats.total_properties || 0, 
              icon: '🏠',
              color: 'from-blue-400 to-blue-600'
            },
            { 
              label: 'With 360° Tours', 
              value: stats.properties_with_tours || 0, 
              icon: '🔄',
              color: 'from-purple-400 to-purple-600'
            },
            { 
              label: 'Total Views', 
              value: stats.total_views || 0, 
              icon: '👀',
              color: 'from-green-400 to-green-600'
            },
            { 
              label: 'Tour Views', 
              value: stats.total_tour_views || 0, 
              icon: '🎯',
              color: 'from-orange-400 to-orange-600'
            },
            { 
              label: 'Total Shares', 
              value: stats.total_shares || 0, 
              icon: '📤',
              color: 'from-pink-400 to-pink-600'
            }
          ].map((stat, index) => (
            <motion.div
              key={index}
              whileHover={{ y: -5 }}
              className="glass rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl">{stat.icon}</span>
                <div className={`text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r ${stat.color}`}>
                  {stat.value}
                </div>
              </div>
              <p className="text-sm opacity-80">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Properties Section */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Your Properties</h2>
            <button
              onClick={() => navigate('/create-property')}
              className="text-purple-300 hover:text-white transition-colors"
            >
              + Add New Property
            </button>
          </div>

          {properties.length === 0 ? (
            <div className="glass rounded-xl p-12 text-center">
              <div className="text-6xl mb-4">🏠</div>
              <h3 className="text-xl font-semibold mb-2">No properties yet</h3>
              <p className="opacity-80 mb-6">Create your first property listing to get started</p>
              <button
                onClick={() => navigate('/create-property')}
                className="btn-viral"
              >
                Create First Property
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {properties.map((property, index) => (
                <motion.div
                  key={property.id}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ y: -5 }}
                  className="glass rounded-xl p-6"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-semibold mb-1">{property.title}</h3>
                      <p className="text-sm opacity-80">{property.address}</p>
                      <p className="text-lg font-bold text-green-400 mt-2">{property.price}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">
                        {property.property_type === 'house' ? '🏠' : 
                         property.property_type === 'apartment' ? '🏢' : '🏘️'}
                      </span>
                      {property.has_tour && (
                        <span className="text-lg" title="Has 360° Tour">🔄</span>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2 text-sm opacity-80 mb-4">
                    {property.bedrooms && <span>🛏️ {property.bedrooms}</span>}
                    {property.bathrooms && <span>🚿 {property.bathrooms}</span>}
                    {property.square_feet && <span>📐 {property.square_feet}ft²</span>}
                  </div>

                  {property.has_tour && (
                    <div className="bg-purple-500/20 rounded-lg p-3 mb-4 text-center">
                      <span className="text-purple-200 text-sm">360° Virtual Tour Available</span>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => generateViralContent(property.id)}
                      className="btn-viral text-sm py-2"
                    >
                      Generate Content
                    </button>
                    {property.has_tour ? (
                      <button
                        onClick={() => viewTour(property.id)}
                        className="px-3 py-2 bg-purple-500 rounded-lg hover:bg-purple-600 transition-all text-sm"
                      >
                        🔄 View Tour
                      </button>
                    ) : (
                      <button
                        onClick={() => navigate(`/upload-tour/${property.id}`)}
                        className="px-3 py-2 border border-white/30 rounded-lg hover:bg-white/10 transition-all text-sm"
                      >
                        + Add Tour
                      </button>
                    )}
                  </div>

                  <div className="mt-2">
                    <button
                      onClick={() => navigate(`/analytics/${property.id}`)}
                      className="w-full px-3 py-2 border border-white/20 rounded-lg hover:bg-white/10 transition-all text-sm"
                    >
                      📊 Analytics
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
