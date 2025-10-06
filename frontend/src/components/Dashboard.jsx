import React, { useState, useEffect, useContext, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { UserContext } from '../App';
import axios from 'axios';
import toast from 'react-hot-toast';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement);

ChartJS.defaults.color = '#e0e0e0';
ChartJS.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

const API = process.env.REACT_APP_BACKEND_URL + '/api' || 'http://localhost:8000/api';

const Dashboard = () => {
  const { user, logout } = useContext(UserContext);
  const navigate = useNavigate();
  const [properties, setProperties] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [leads, setLeads] = useState([]);
  const [tourEngagement, setTourEngagement] = useState({});

  // Fetch all dashboard data
  const fetchDashboardData = useCallback(async () => {
    if (!user?.id) return;
    try {
      const [propertiesRes, dashboardRes] = await Promise.all([
        axios.get(`${API}/properties/${user.id}`),
        axios.get(`${API}/dashboard/${user.id}`)
      ]);
      setProperties(propertiesRes.data);
      setStats(dashboardRes.data.stats || {});
      
      // Mock lead data - replace with real API call
      setLeads([
        { id: 1, name: 'Sarah Johnson', email: 'sarah@email.com', property: propertiesRes.data[0]?.title || 'Property', status: 'hot', time: '2 hours ago', source: 'Instagram' },
        { id: 2, name: 'Mike Chen', email: 'mike@email.com', property: propertiesRes.data[0]?.title || 'Property', status: 'warm', time: '5 hours ago', source: 'Facebook' },
        { id: 3, name: 'Jessica Smith', email: 'jessica@email.com', property: propertiesRes.data[1]?.title || 'Property', status: 'cold', time: '1 day ago', source: 'TikTok' }
      ]);

      // Mock tour engagement - replace with real API call
      setTourEngagement({
        total_tour_views: 1247,
        avg_duration: '3:42',
        completion_rate: 67,
        most_viewed_room: 'Master Bedroom',
        peak_hours: '6-8 PM'
      });

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

  const quickShare = (property, platform) => {
    const shareUrls = {
      instagram: `https://www.instagram.com/`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${window.location.origin}/tour/${property.id}`,
      twitter: `https://twitter.com/intent/tweet?text=Check out this property!&url=${window.location.origin}/tour/${property.id}`,
      tiktok: `https://www.tiktok.com/`
    };
    window.open(shareUrls[platform], '_blank');
    toast.success(`Opening ${platform}...`);
  };

  const getPlanFeatures = (plan) => {
    const features = {
      starter: { maxProperties: 5, contentGenerations: 50, analytics: 'Basic', leadTracking: false },
      professional: { maxProperties: 'Unlimited', contentGenerations: 500, analytics: 'Advanced', leadTracking: true },
      enterprise: { maxProperties: 'Unlimited', contentGenerations: 'Unlimited', analytics: 'Premium', leadTracking: true }
    };
    return features[plan] || features.starter;
  };
  const planLimits = getPlanFeatures(user?.plan || 'starter');

  // Chart data
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
        label: 'Leads',
        data: properties.slice(0, 5).map(() => Math.floor(Math.random() * 50) + 5),
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 2,
        borderRadius: 5,
      }
    ]
  };

  const engagementTrendData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'Tour Views',
      data: [65, 78, 90, 81, 96, 105, 92],
      borderColor: 'rgb(192, 132, 252)',
      backgroundColor: 'rgba(192, 132, 252, 0.1)',
      tension: 0.4,
      fill: true
    }]
  };

  const platformDistribution = {
    labels: ['Instagram', 'TikTok', 'Facebook', 'Twitter'],
    datasets: [{
      data: [35, 30, 20, 15],
      backgroundColor: ['#E4405F', '#000000', '#1877F2', '#1DA1F2'],
      borderWidth: 0
    }]
  };

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header with Quick Actions */}
        <div className="flex flex-wrap justify-between items-center gap-4 mb-8">
          <div>
            <motion.h1 initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="text-3xl font-bold mb-2">
              Welcome back, {user?.name}!
            </motion.h1>
            <p className="text-purple-200">You have {leads.length} new leads this week</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/create-property')} className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition-all">
              + New Property
            </button>
            <button onClick={logout} className="border border-white/30 rounded-lg px-4 py-3 hover:bg-white/10 transition-all">
              Logout
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-8 bg-white/5 p-1 rounded-xl backdrop-blur-sm w-fit">
          {['overview', 'leads', 'engagement'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 rounded-lg capitalize transition-all ${
                activeTab === tab 
                  ? 'bg-white/20 font-semibold' 
                  : 'hover:bg-white/10'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              {/* Enhanced Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {[
                  { label: 'Total Properties', value: stats.total_properties || 0, icon: '🏠', change: '+2 this month', color: 'from-blue-400 to-blue-600' },
                  { label: 'Active Leads', value: leads.length, icon: '👥', change: '+12 this week', color: 'from-green-400 to-green-600' },
                  { label: 'Tour Views', value: tourEngagement.total_tour_views || 0, icon: '👁️', change: '+23% vs last week', color: 'from-purple-400 to-purple-600' },
                  { label: 'Conversion Rate', value: `${tourEngagement.completion_rate || 0}%`, icon: '📈', change: '+5% improvement', color: 'from-orange-400 to-orange-600' }
                ].map((stat, index) => (
                  <motion.div key={index} whileHover={{ y: -5 }} className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-3xl">{stat.icon}</span>
                      <div className={`text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r ${stat.color}`}>
                        {stat.value}
                      </div>
                    </div>
                    <p className="text-sm opacity-90 font-medium">{stat.label}</p>
                    <p className="text-xs text-green-400 mt-1">{stat.change}</p>
                  </motion.div>
                ))}
              </div>

              {/* Main Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Properties List (2 columns) */}
                <div className="lg:col-span-2">
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold">Your Properties</h2>
                    <button onClick={() => navigate('/create-property')} className="text-purple-300 hover:text-white transition-colors">
                      + Add Property
                    </button>
                  </div>

                  {properties.length === 0 ? (
                    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-12 text-center border border-white/20">
                      <div className="text-6xl mb-4">🏠</div>
                      <h3 className="text-xl font-semibold mb-2">No properties yet</h3>
                      <p className="opacity-80 mb-6">Create your first property to start generating leads</p>
                      <button onClick={() => navigate('/create-property')} className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-3 rounded-lg font-semibold">
                        Create First Property
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {properties.map((property, index) => (
                        <motion.div
                          key={property.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:border-purple-400 transition-all"
                        >
                          <div className="flex flex-col md:flex-row gap-4">
                            {/* Property Info */}
                            <div className="flex-grow">
                              <div className="flex items-start justify-between mb-3">
                                <div>
                                  <h3 className="font-semibold text-lg mb-1">{property.title}</h3>
                                  <p className="text-sm opacity-80">{property.address}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-2xl">{property.property_type === 'house' ? '🏠' : '🏢'}</span>
                                  {property.has_tour && <span className="bg-purple-500 px-2 py-1 rounded text-xs">360° Tour</span>}
                                </div>
                              </div>

                              <div className="flex gap-4 text-sm opacity-90 mb-3">
                                <span className="font-bold text-green-400 text-lg">{property.price}</span>
                                {property.bedrooms && <span>🛏️ {property.bedrooms}</span>}
                                {property.bathrooms && <span>🚿 {property.bathrooms}</span>}
                                {property.square_feet && <span>📐 {property.square_feet}ft²</span>}
                              </div>

                              {/* Quick Stats */}
                              <div className="flex gap-4 text-xs bg-white/5 rounded-lg p-2">
                                <span>👁️ {Math.floor(Math.random() * 500) + 50} views</span>
                                <span>👥 {Math.floor(Math.random() * 20) + 1} leads</span>
                                <span>📤 {Math.floor(Math.random() * 50) + 5} shares</span>
                              </div>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex flex-col gap-2 min-w-[200px]">
                              <button
                                onClick={() => generateViralContent(property.id)}
                                className="bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-2 rounded-lg font-medium hover:shadow-lg transition-all text-sm"
                              >
                                🚀 Generate Content
                              </button>
                              
                              {property.has_tour ? (
                                <button
                                  onClick={() => navigate(`/virtual-tour/${property.id}`)}
                                  className="bg-purple-600 px-4 py-2 rounded-lg hover:bg-purple-700 transition-all text-sm"
                                >
                                  🔄 View Tour
                                </button>
                              ) : (
                                <button
                                  onClick={() => navigate(`/upload-tour/${property.id}`)}
                                  className="border border-white/30 px-4 py-2 rounded-lg hover:bg-white/10 transition-all text-sm"
                                >
                                  + Add Tour
                                </button>
                              )}

                              {/* Quick Share */}
                              <div className="flex gap-1">
                                <button onClick={() => quickShare(property, 'instagram')} className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 p-2 rounded text-xs">IG</button>
                                <button onClick={() => quickShare(property, 'facebook')} className="flex-1 bg-blue-600 p-2 rounded text-xs">FB</button>
                                <button onClick={() => quickShare(property, 'tiktok')} className="flex-1 bg-black p-2 rounded text-xs">TT</button>
                              </div>

                              <button
                                onClick={() => navigate(`/analytics/${property.id}`)}
                                className="border border-white/20 px-4 py-2 rounded-lg hover:bg-white/10 transition-all text-sm"
                              >
                                📊 Analytics
                              </button>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Sidebar (1 column) */}
                <div className="space-y-6">
                  {/* Performance Chart */}
                  <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                    <h3 className="text-lg font-bold mb-4">Weekly Engagement</h3>
                    <Line 
                      data={engagementTrendData} 
                      options={{ 
                        responsive: true, 
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true } }
                      }} 
                    />
                  </div>

                  {/* Platform Distribution */}
                  <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                    <h3 className="text-lg font-bold mb-4">Traffic Sources</h3>
                    <Doughnut data={platformDistribution} options={{ plugins: { legend: { position: 'bottom' } } }} />
                  </div>

                  {/* Plan Usage */}
                  <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                    <h3 className="text-lg font-bold mb-4">Plan Usage</h3>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Properties</span>
                          <span>{properties.length} / {planLimits.maxProperties}</span>
                        </div>
                        <div className="w-full bg-white/10 rounded-full h-2">
                          <div className="bg-purple-400 h-2 rounded-full" style={{ width: planLimits.maxProperties === 'Unlimited' ? '20%' : `${(properties.length / planLimits.maxProperties) * 100}%` }} />
                        </div>
                      </div>
                    </div>
                    {user?.plan === 'starter' && (
                      <button onClick={() => navigate('/pricing')} className="w-full mt-4 bg-gradient-to-r from-purple-500 to-pink-500 py-2 rounded-lg font-medium">
                        Upgrade Plan
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'leads' && (
            <motion.div
              key="leads"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                <h2 className="text-2xl font-bold mb-6">Recent Leads</h2>
                
                {!planLimits.leadTracking ? (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">🔒</div>
                    <h3 className="text-xl font-bold mb-2">Upgrade to Track Leads</h3>
                    <p className="opacity-80 mb-6">Get detailed lead tracking with Professional plan</p>
                    <button onClick={() => navigate('/pricing')} className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-3 rounded-lg font-semibold">
                      Upgrade Now
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {leads.map((lead) => (
                      <div key={lead.id} className="bg-white/5 p-4 rounded-lg flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center font-bold">
                              {lead.name.charAt(0)}
                            </div>
                            <div>
                              <h4 className="font-semibold">{lead.name}</h4>
                              <p className="text-sm opacity-80">{lead.email}</p>
                            </div>
                          </div>
                          <p className="text-sm mt-2 opacity-90">Interested in: {lead.property}</p>
                          <p className="text-xs opacity-70">Source: {lead.source} • {lead.time}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            lead.status === 'hot' ? 'bg-red-500' : 
                            lead.status === 'warm' ? 'bg-yellow-500' : 'bg-blue-500'
                          }`}>
                            {lead.status.toUpperCase()}
                          </span>
                          <button className="bg-white/10 px-4 py-2 rounded-lg hover:bg-white/20 transition-all text-sm">
                            Contact
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'engagement' && (
            <motion.div
              key="engagement"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                  <h3 className="text-lg font-bold mb-4">Tour Engagement</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="opacity-80">Avg. Duration</span>
                      <span className="font-bold text-xl">{tourEngagement.avg_duration}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="opacity-80">Completion Rate</span>
                      <span className="font-bold text-xl">{tourEngagement.completion_rate}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="opacity-80">Most Viewed Room</span>
                      <span className="font-bold">{tourEngagement.most_viewed_room}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="opacity-80">Peak Hours</span>
                      <span className="font-bold">{tourEngagement.peak_hours}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                  <h3 className="text-lg font-bold mb-4">Property Performance</h3>
                  <Bar data={performanceChartData} options={{ responsive: true, plugins: { legend: { position: 'top' } } }} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Dashboard;
