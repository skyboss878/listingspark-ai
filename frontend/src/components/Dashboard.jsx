import React, { useState, useEffect, useContext, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { UserContext } from '../App';
import axios from 'axios';
import toast from 'react-hot-toast';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

// Configure Chart.js defaults for a dark theme
ChartJS.defaults.color = '#e0e0e0';
ChartJS.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';


const API = process.env.REACT_APP_BACKEND_URL + '/api' || 'http://localhost:8000/api';

const Dashboard = () => {
  const { user, logout } = useContext(UserContext);
  const navigate = useNavigate();
  const [properties, setProperties] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  // --- Data Fetching ---
  const fetchDashboardData = useCallback(async () => {
    if (!user?.id) return;
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

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // --- Actions ---
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

  const viewTour = (propertyId) => navigate(`/virtual-tour/${propertyId}`);

  // --- Plan & Chart Logic ---
  const getPlanFeatures = (plan) => {
    const features = {
      starter: { maxProperties: 5, contentGenerations: 50, analytics: 'Basic' },
      professional: { maxProperties: 'Unlimited', contentGenerations: 500, analytics: 'Advanced' },
      enterprise: { maxProperties: 'Unlimited', contentGenerations: 'Unlimited', analytics: 'Premium' }
    };
    return features[plan] || features.starter;
  };
  const planLimits = getPlanFeatures(user?.plan || 'starter');

  const performanceChartData = {
    labels: properties.slice(0, 5).map(p => p.title.length > 15 ? `${p.title.substring(0, 15)}...` : p.title),
    datasets: [
      {
        label: 'Views',
        data: properties.slice(0, 5).map(() => Math.floor(Math.random() * 1000) + 100),
        backgroundColor: 'rgba(192, 132, 252, 0.2)',
        borderColor: 'rgb(192, 132, 252)',
        borderWidth: 2,
        borderRadius: 5,
      },
      {
        label: 'Shares',
        data: properties.slice(0, 5).map(() => Math.floor(Math.random() * 200) + 20),
        backgroundColor: 'rgba(139, 92, 246, 0.2)',
        borderColor: 'rgb(139, 92, 246)',
        borderWidth: 2,
        borderRadius: 5,
      }
    ]
  };

  // --- Loading State ---
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-12 h-12 border-4 border-purple-400 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  // --- Render Component ---
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-center gap-4 mb-8">
          <div>
            <motion.h1 initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="text-3xl font-bold mb-2">
              Welcome back, {user?.name}! 👋
            </motion.h1>
            <p className="text-purple-200">Ready to create more viral content with 360° tours?</p>
          </div>
          <div className="flex items-center gap-4">
             <button onClick={() => navigate('/create-property')} className="btn-viral whitespace-nowrap">
              + New Property
            </button>
            <button onClick={logout} className="border border-white/30 rounded-lg px-4 py-2 hover:bg-white/10 transition-all">
              Logout
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8">
          {[
            { label: 'Total Properties', value: stats.total_properties || 0, icon: '🏠', color: 'from-blue-400 to-blue-600' },
            { label: 'With 360° Tours', value: stats.properties_with_tours || 0, icon: '🔄', color: 'from-purple-400 to-purple-600' },
            { label: 'Total Views', value: stats.total_views || 0, icon: '👀', color: 'from-green-400 to-green-600' },
            { label: 'Total Shares', value: stats.total_shares || 0, icon: '📤', color: 'from-pink-400 to-pink-600' },
            { label: 'Avg. Viral Score', value: Math.round(stats.average_viral_score || 0), icon: '🚀', color: 'from-orange-400 to-orange-600' }
          ].map((stat, index) => (
            <motion.div key={index} whileHover={{ y: -5 }} className="glass rounded-xl p-6">
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

        {/* Main Content: Properties & Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Properties Section */}
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }} className="lg:col-span-3">
            <h2 className="text-2xl font-bold mb-6">Your Properties</h2>
            {properties.length === 0 ? (
              <div className="glass rounded-xl p-12 text-center">
                <div className="text-6xl mb-4">🏠</div>
                <h3 className="text-xl font-semibold mb-2">No properties yet</h3>
                <p className="opacity-80 mb-6">Create your first property listing to get started</p>
                <button onClick={() => navigate('/create-property')} className="btn-viral">
                  Create First Property
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {properties.map((property, index) => (
                  <motion.div key={property.id} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: index * 0.1 }} whileHover={{ y: -5 }} className="glass rounded-xl p-6 flex flex-col">
                    <div className="flex-grow">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="font-semibold mb-1">{property.title}</h3>
                          <p className="text-sm opacity-80">{property.address}</p>
                          <p className="text-lg font-bold text-green-400 mt-2">{property.price}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{property.property_type === 'house' ? '🏠' : '🏢'}</span>
                          {property.has_tour && <span className="text-lg" title="Has 360° Tour">🔄</span>}
                        </div>
                      </div>
                      <div className="flex gap-2 text-sm opacity-80 mb-4">
                        {property.bedrooms && <span>🛏️ {property.bedrooms}</span>}
                        {property.bathrooms && <span>🚿 {property.bathrooms}</span>}
                        {property.square_feet && <span>📐 {property.square_feet}ft²</span>}
                      </div>
                    </div>
                    <div>
                      <div className="grid grid-cols-2 gap-2 mb-2">
                        <button onClick={() => generateViralContent(property.id)} className="btn-viral text-sm py-2">
                          Generate Content
                        </button>
                        {property.has_tour ? (
                          <button onClick={() => viewTour(property.id)} className="px-3 py-2 bg-purple-500 rounded-lg hover:bg-purple-600 transition-all text-sm">
                            🔄 View Tour
                          </button>
                        ) : (
                          <button onClick={() => navigate(`/upload-tour/${property.id}`)} className="px-3 py-2 border border-white/30 rounded-lg hover:bg-white/10 transition-all text-sm">
                            + Add Tour
                          </button>
                        )}
                      </div>
                      <button onClick={() => navigate(`/analytics/${property.id}`)} className="w-full px-3 py-2 border border-white/20 rounded-lg hover:bg-white/10 transition-all text-sm">
                        📊 Analytics
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Side Column: Performance & Plan */}
          <div className="lg:col-span-2 space-y-8">
            {/* Performance Chart */}
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }} className="glass rounded-xl p-6">
              <h3 className="text-xl font-bold mb-4">Performance Overview</h3>
              {properties.length > 0 ? (
                <Bar data={performanceChartData} options={{ responsive: true, plugins: { legend: { position: 'top' } } }} />
              ) : (
                <div className="text-center py-8">
                  <div className="text-6xl mb-4">📊</div>
                  <p className="opacity-80">Add properties to see performance data</p>
                </div>
              )}
            </motion.div>

            {/* Plan Usage */}
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4 }} className="glass rounded-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold">Plan Usage</h3>
                <button onClick={() => navigate('/#pricing')} className="text-purple-300 hover:text-white font-medium transition-colors">
                  Upgrade Plan
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2 text-sm">
                    <span>Properties</span>
                    <span className="font-medium">{properties.length} / {planLimits.maxProperties}</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <div className="bg-purple-400 h-2 rounded-full" style={{ width: planLimits.maxProperties === 'Unlimited' ? '20%' : `${(properties.length / planLimits.maxProperties) * 100}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2 text-sm">
                    <span>Content Generations</span>
                    <span className="font-medium">{stats.content_generations_this_month || 0} / {planLimits.contentGenerations}</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <div className="bg-green-400 h-2 rounded-full" style={{ width: '15%' }} />
                  </div>
                </div>
              </div>
              {user?.plan === 'starter' && (
                <div className="mt-6 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-lg p-4 flex items-center gap-4">
                  <div className="text-2xl">🚀</div>
                  <div>
                    <h4 className="font-medium">Ready to go viral?</h4>
                    <p className="text-sm opacity-80">Upgrade for unlimited properties & advanced AI.</p>
                  </div>
                  <button onClick={() => navigate('/#pricing')} className="ml-auto btn-viral text-sm py-2 px-3 whitespace-nowrap">
                    Upgrade
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
