// ============================================
// PART 1: Enhanced Dashboard.jsx with MLS Integration
// Save as: src/components/Dashboard.jsx
// ============================================

import React, { useState, useEffect, useContext, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
// Charts imported but not used yet
// import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { UserContext } from '../App';
import axios from '../api';
import toast from 'react-hot-toast';
import TrialBanner from './TrialBanner';
import { Share2, Facebook, Twitter, Instagram, Linkedin, Copy } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement);
ChartJS.defaults.color = '#e0e0e0';
ChartJS.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

// Enhanced API client with auth token
const api = axios.create({
  baseURL: (process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000') + '/api',
});

// Add token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const Dashboard = () => {
  const { user, logout } = useContext(UserContext);
  const navigate = useNavigate();
  const [listings, setListings] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  // eslint-disable-next-line no-unused-vars
  const [activeTab, setActiveTab] = useState('overview');
  const [mlsAccounts, setMLSAccounts] = useState([]);
  const [systemFeatures, setSystemFeatures] = useState({});
  const [socialMenuOpen, setSocialMenuOpen] = useState(null);

  // Fetch all dashboard data from NEW backend
  const fetchDashboardData = useCallback(async () => {
    if (!user?.id) return;
    
    // Fetch listings (most important)
    try {
      const listingsRes = await api.get('/listings');
      setListings(listingsRes.data);
    } catch (error) {
      console.error('Error fetching listings:', error);
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        logout();
        navigate('/login');
        return;
      }
      setListings([]);
    }
    
    // Fetch other data with individual error handling
    try {
      const statsRes = await api.get('/dashboard/stats');
      setStats(statsRes.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setStats({});
    }
    
    try {
      const mlsRes = await api.get('/mls/accounts');
      setMLSAccounts(mlsRes.data);
    } catch (error) {
      console.error('Error fetching MLS accounts:', error);
      setMLSAccounts([]);
    }
    
    try {
      const featuresRes = await api.get('/system/features');
      setSystemFeatures(featuresRes.data);
    } catch (error) {
      console.error('Error fetching system features:', error);
      setSystemFeatures({});
    }
    
    setLoading(false);
  }, [user, logout, navigate]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Generate AI content for listing
  const generateAIContent = async (listingId) => {
    try {
      toast.loading('🤖 Generating AI content...', { id: 'ai-gen' });
      await api.post(`/content/generate/${listingId}`, {
        listing_id: listingId,
        include_social_media: true,
        include_email_template: true,
        tone: 'professional'
      });
      toast.success('✨ AI content generated!', { id: 'ai-gen' });
      fetchDashboardData();
    } catch (error) {
      toast.error('Failed to generate AI content', { id: 'ai-gen' });
    }
  };

  // Generate 360° virtual tour
  const generateVirtualTour = async (listingId) => {
    try {
      toast.loading('🎥 Generating 360° tour...', { id: 'tour-gen' });
      await api.post(`/tours/generate/${listingId}`, {
        listing_id: listingId,
        style: 'cinematic',
        voice_style: 'professional',
        enable_360_camera: true,
        enable_narration: true
      });
      toast.success('🎬 Virtual tour is being generated!', { id: 'tour-gen' });
      
      // Poll for tour status
      pollTourStatus(listingId);
    } catch (error) {
      toast.error('Failed to generate tour', { id: 'tour-gen' });
    }
  };

  // Poll tour generation status
  const pollTourStatus = async (listingId) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/tours/${listingId}/status`);
        if (response.data.status === 'completed') {
          clearInterval(interval);
          toast.success('🎉 Virtual tour ready!');
          fetchDashboardData();
        } else if (response.data.status === 'failed') {
          clearInterval(interval);
          toast.error('Tour generation failed');
        }
      } catch (error) {
        clearInterval(interval);
      }
    }, 5000);

    // Stop polling after 5 minutes
    setTimeout(() => clearInterval(interval), 300000);
  };

  // Complete workflow: AI + Tour + Enhancement
  const completeWorkflow = async (listingId) => {
    try {
      toast.loading('🚀 Running complete workflow...', { id: 'workflow' });
      await api.post(`/workflow/complete/${listingId}`, {
        tour_style: 'cinematic',
        voice_style: 'professional',
        ai_tone: 'professional'
      });
      toast.success('✨ Workflow started! This may take a few minutes.', { id: 'workflow' });
      
      // Poll for completion
      const interval = setInterval(async () => {
        try {
          const response = await api.get(`/workflow/status/${listingId}`);
          if (response.data.steps_completed.ready_to_publish) {
            clearInterval(interval);
            toast.success('🎉 Listing is ready to publish!');
            fetchDashboardData();
          }
        } catch (error) {
          clearInterval(interval);
        }
      }, 10000);

      setTimeout(() => clearInterval(interval), 600000); // 10 min timeout
    } catch (error) {
      toast.error('Workflow failed', { id: 'workflow' });
    }
  };

  // Publish to MLS
  const publishToMLS = async (listingId) => {
    if (mlsAccounts.length === 0) {
      toast.error('Please connect an MLS account first');
      navigate('/mls-setup');
      return;
    }

    try {
      toast.loading('📤 Publishing to MLS...', { id: 'publish' });
      await api.post('/mls/publish', {
        listing_id: listingId,
        mls_account_id: mlsAccounts[0].id
      });
      toast.success('✅ Published to MLS! Syndicating to portals...', { id: 'publish' });
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to publish', { id: 'publish' });
    }
  };

  // Social media sharing
  const shareToSocialMedia = (listing, platform) => {
    const listingUrl = `${window.location.origin}/listing/${listing.id}`;
    const text = `Check out this property: ${listing.address}, ${listing.city} - $${listing.price?.toLocaleString()}`;
    
    const urls = {
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(listingUrl)}`,
      twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(listingUrl)}&text=${encodeURIComponent(text)}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(listingUrl)}`,
      instagram: listingUrl
    };

    if (platform === 'instagram' || platform === 'copy') {
      // Fallback for clipboard API
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(listingUrl).then(() => {
            toast.success('Link copied to clipboard!');
          }).catch(() => {
            // Fallback method
            const textArea = document.createElement('textarea');
            textArea.value = listingUrl;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            try {
              document.execCommand('copy');
              toast.success('Link copied to clipboard!');
            } catch (err) {
              toast.error('Could not copy link. Please copy manually: ' + listingUrl);
            }
            document.body.removeChild(textArea);
          });
        } else {
          // Old browser fallback
          const textArea = document.createElement('textarea');
          textArea.value = listingUrl;
          textArea.style.position = 'fixed';
          textArea.style.left = '-999999px';
          document.body.appendChild(textArea);
          textArea.select();
          document.execCommand('copy');
          document.body.removeChild(textArea);
          toast.success('Link copied to clipboard!');
        }
      } catch (err) {
        prompt('Copy this link:', listingUrl);
      }
    } else {
      window.open(urls[platform], '_blank', 'width=600,height=400');
      toast.success(`Opening ${platform}...`);
    }
    
    setSocialMenuOpen(null);
  };

  // Get status badge
  const getStatusBadge = (status) => {
    const badges = {
      draft: { color: 'bg-gray-500', text: 'Draft', icon: '📝' },
      images_uploaded: { color: 'bg-blue-500', text: 'Images Uploaded', icon: '🖼️' },
      ai_enhanced: { color: 'bg-purple-500', text: 'AI Enhanced', icon: '🤖' },
      tour_generating: { color: 'bg-yellow-500', text: 'Generating Tour', icon: '⚙️' },
      tour_generated: { color: 'bg-green-500', text: 'Tour Ready', icon: '🎬' },
      ready_to_publish: { color: 'bg-cyan-500', text: 'Ready to Publish', icon: '✅' },
      published: { color: 'bg-emerald-500', text: 'Published', icon: '🚀' },
      syndicated: { color: 'bg-pink-500', text: 'Syndicated', icon: '🌐' },
    };
    return badges[status] || badges.draft;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-16 h-16 border-4 border-purple-400 border-t-transparent rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-xl">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Trial Banner */}
        <TrialBanner />
        
        {/* Enhanced Header */}
        <div className="flex flex-wrap justify-between items-center gap-4 mb-8">
          <div>
            <motion.h1 initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Welcome back, {user?.full_name || user?.name}!
            </motion.h1>
            <p className="text-purple-200 flex items-center gap-2">
              <span className="text-2xl">🎉</span>
              You have {stats.total_listings || 0} listings • {stats.published_listings || 0} published
            </p>
          </div>
          <div className="flex items-center gap-3">
            {mlsAccounts.length === 0 && (
              <button 
                onClick={() => navigate('/mls-setup')}
                className="bg-gradient-to-r from-orange-500 to-red-500 px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition-all animate-pulse"
              >
                🔗 Connect MLS
              </button>
            )}
            <button 
              onClick={() => navigate('/create-listing')} 
              className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition-all"
            >
              ✨ New Listing
            </button>
            <button 
              onClick={logout} 
              className="border border-white/30 rounded-lg px-4 py-3 hover:bg-white/10 transition-all"
            >
              Logout
            </button>
          </div>
        </div>

        {/* System Features Banner */}
        {systemFeatures && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 backdrop-blur-sm rounded-xl p-4 mb-6 border border-purple-500/30"
          >
            <div className="flex flex-wrap gap-4 items-center justify-center text-sm">
              {systemFeatures.video_tours?.available && (
                 <span className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                
                  </span>
              )}
              {systemFeatures.ai_content?.available && (
                <span className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  AI Content (GPT-4)
                </span>
              )}
              {systemFeatures.voice_narration?.available && (
                <span className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  Voice Narration
                </span>
              )}
              {systemFeatures.mls_integration?.available && (
                <span className="flex items-center gap-2">
                  <span className="text-green-400">✓</span>
                  MLS Integration
                </span>
              )}
            </div>
          </motion.div>
        )}

        {/* Enhanced Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          {[
            { label: 'Total Listings', value: stats.total_listings || 0, icon: '🏠', change: `${stats.draft_listings || 0} drafts`, color: 'from-blue-400 to-blue-600' },
            { label: 'AI Enhanced', value: stats.ai_enhanced || 0, icon: '🤖', change: 'Ready for tours', color: 'from-purple-400 to-purple-600' },
            { label: 'Tours Generated', value: stats.tour_generated || 0, icon: '🎬', change: 'With 360° camera', color: 'from-pink-400 to-pink-600' },
            { label: 'Published', value: stats.published_listings || 0, icon: '🚀', change: 'Live on MLS', color: 'from-green-400 to-green-600' },
            { label: 'MLS Accounts', value: mlsAccounts.length, icon: '🔗', change: mlsAccounts.length > 0 ? 'Connected' : 'Not connected', color: 'from-orange-400 to-orange-600' }
          ].map((stat, index) => (
            <motion.div 
              key={index} 
              whileHover={{ y: -5, scale: 1.02 }} 
              className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:border-purple-400 transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-4xl">{stat.icon}</span>
                <div className={`text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r ${stat.color}`}>
                  {stat.value}
                </div>
              </div>
              <p className="text-sm opacity-90 font-medium mb-1">{stat.label}</p>
              <p className="text-xs text-purple-300">{stat.change}</p>
            </motion.div>
          ))}
        </div>

        {/* Listings Grid - Enhanced */}
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-3xl font-bold">Your Listings</h2>
            <div className="flex gap-2">
              <button 
                onClick={() => navigate('/create-listing')}
                className="bg-purple-600 px-4 py-2 rounded-lg hover:bg-purple-700 transition-all text-sm"
              >
                + New Listing
              </button>
            </div>
          </div>

          {listings.length === 0 ? (
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-12 text-center border border-white/20">
              <div className="text-8xl mb-4">🏠</div>
              <h3 className="text-2xl font-semibold mb-3">No listings yet</h3>
              <p className="opacity-80 mb-6 text-lg">Create your first listing with AI-powered content and 360° tours</p>
              <button 
                onClick={() => navigate('/create-listing')} 
                className="bg-gradient-to-r from-purple-500 to-pink-500 px-8 py-4 rounded-lg font-semibold text-lg hover:shadow-2xl transition-all"
              >
                ✨ Create First Listing
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {listings.map((listing, index) => {
                const status = getStatusBadge(listing.status);
                return (
                  <motion.div
                    key={listing.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white/10 backdrop-blur-sm rounded-xl overflow-hidden border border-white/20 hover:border-purple-400 transition-all group"
                  >
                    {/* Listing Image */}
                    <div className="relative h-48 bg-gradient-to-br from-purple-900/50 to-blue-900/50 overflow-hidden">
                      {listing.images && listing.images.length > 0 ? (
                        <img 
                          src={listing.images[0]} 
                          alt={listing.address}
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-6xl">
                          🏠
                        </div>
                      )}
                      <div className="absolute top-4 right-4 flex gap-2">
                        <span className={`${status.color} px-3 py-1 rounded-full text-xs font-bold`}>
                          {status.icon} {status.text}
                        </span>
                        {listing.virtual_tour && (
                          <span className="bg-purple-600 px-3 py-1 rounded-full text-xs font-bold">
                            🎥 360° Tour
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Listing Info */}
                    <div className="p-6">
                      <h3 className="font-bold text-xl mb-2">{listing.address}</h3>
                      <p className="text-purple-200 mb-3">{listing.city}, {listing.state}</p>
                      
                      <div className="flex gap-4 text-sm mb-4">
                        <span className="font-bold text-green-400 text-2xl">${listing.price?.toLocaleString()}</span>
                      </div>

                      <div className="flex gap-4 text-sm opacity-90 mb-4">
                        <span>🛏️ {listing.bedrooms} beds</span>
                        <span>🚿 {listing.bathrooms} baths</span>
                        <span>📐 {listing.square_feet?.toLocaleString()} ft²</span>
                      </div>

                      {/* Action Buttons */}
                      <div className="space-y-2">
                        {listing.status === 'draft' || listing.status === 'images_uploaded' ? (
                          <button
                            onClick={() => completeWorkflow(listing.id)}
                            className="w-full bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-3 rounded-lg font-semibold hover:shadow-lg transition-all"
                          >
                            🚀 Complete Workflow (AI + Tour + Enhance)
                          </button>
                        ) : listing.status === 'ready_to_publish' ? (
                          <button
                            onClick={() => publishToMLS(listing.id)}
                            className="w-full bg-gradient-to-r from-green-500 to-emerald-500 px-4 py-3 rounded-lg font-semibold hover:shadow-lg transition-all"
                          >
                            📤 Publish to MLS
                          </button>
                        ) : listing.status === 'published' || listing.status === 'syndicated' ? (
                          <div className="bg-green-500/20 border border-green-500 rounded-lg p-3 text-center">
                            <p className="font-semibold">✅ Published to MLS</p>
                            <p className="text-xs opacity-80">Syndicating to portals...</p>
                          </div>
                        ) : null}

                        <div className="grid grid-cols-2 gap-2">
                          {!listing.ai_content && (
                            <button
                              onClick={() => generateAIContent(listing.id)}
                              className="bg-purple-600 px-4 py-2 rounded-lg hover:bg-purple-700 transition-all text-sm"
                            >
                              🤖 AI Content
                            </button>
                          )}
                          {!listing.virtual_tour && listing.images?.length > 0 && (
                            <button
                              onClick={() => generateVirtualTour(listing.id)}
                              className="bg-pink-600 px-4 py-2 rounded-lg hover:bg-pink-700 transition-all text-sm"
                            >
                              🎬 360° Tour
                            </button>
                          )}
                          {listing.virtual_tour && (
                            <button
                              onClick={() => navigate(`/virtual-tour/${listing.id}`)}
                              className="bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-700 transition-all text-sm col-span-2"
                            >
                              👁️ View Tour
                            </button>
                          )}
                        </div>

                        {/* Social Media Share Dropdown */}
                        <div className="relative mt-2">
                          <button
                            onClick={() => setSocialMenuOpen(socialMenuOpen === listing.id ? null : listing.id)}
                            className="w-full bg-indigo-600 px-4 py-2 rounded-lg hover:bg-indigo-700 transition-all text-sm flex items-center justify-center gap-2"
                          >
                            <Share2 className="w-4 h-4" />
                            Share on Social Media
                          </button>
                          
                          {socialMenuOpen === listing.id && (
                            <div className="absolute bottom-full mb-2 left-0 right-0 bg-gray-800 rounded-lg shadow-xl border border-white/20 p-2 z-50">
                              <button
                                onClick={() => shareToSocialMedia(listing, 'facebook')}
                                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-white/10 rounded-lg transition-all text-left"
                              >
                                <Facebook className="w-5 h-5 text-blue-500" />
                                <span>Facebook</span>
                              </button>
                              <button
                                onClick={() => shareToSocialMedia(listing, 'twitter')}
                                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-white/10 rounded-lg transition-all text-left"
                              >
                                <Twitter className="w-5 h-5 text-sky-400" />
                                <span>Twitter/X</span>
                              </button>
                              <button
                                onClick={() => shareToSocialMedia(listing, 'linkedin')}
                                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-white/10 rounded-lg transition-all text-left"
                              >
                                <Linkedin className="w-5 h-5 text-blue-600" />
                                <span>LinkedIn</span>
                              </button>
                              <button
                                onClick={() => shareToSocialMedia(listing, 'instagram')}
                                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-white/10 rounded-lg transition-all text-left"
                              >
                                <Instagram className="w-5 h-5 text-pink-500" />
                                <span>Instagram (Copy Link)</span>
                              </button>
                              <button
                                onClick={() => shareToSocialMedia(listing, 'copy')}
                                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-white/10 rounded-lg transition-all text-left"
                              >
                                <Copy className="w-5 h-5 text-gray-400" />
                                <span>Copy Link</span>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
