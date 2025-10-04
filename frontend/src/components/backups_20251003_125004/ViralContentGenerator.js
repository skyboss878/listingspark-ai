import React, { useState, useEffect, useContext } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { UserContext } from '../App';
import axios from 'axios';
import toast from 'react-hot-toast';

const API = process.env.REACT_APP_BACKEND_URL + '/api' || 'http://localhost:8000/api';

const ViralContentGenerator = () => {
  const { propertyId } = useParams();
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const [property, setProperty] = useState(null);
  const [viralContent, setViralContent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState('all');

  const platforms = [
    { id: 'instagram', name: 'Instagram', icon: '📸', color: 'from-pink-500 to-rose-500' },
    { id: 'tiktok', name: 'TikTok', icon: '🎵', color: 'from-gray-900 to-gray-700' },
    { id: 'facebook', name: 'Facebook', icon: '👥', color: 'from-blue-600 to-blue-800' }
  ];

  useEffect(() => {
    fetchPropertyAndContent();
  }, [propertyId]);

  const fetchPropertyAndContent = async () => {
    try {
      const [propertyRes, contentRes] = await Promise.all([
        axios.get(`${API}/properties/${user.id}`),
        axios.get(`${API}/properties/${propertyId}/viral-content`)
      ]);

      const foundProperty = propertyRes.data.find(p => p.id === propertyId);
      setProperty(foundProperty);
      setViralContent(contentRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load content');
    } finally {
      setLoading(false);
    }
  };

  const generateContent = async () => {
    setGenerating(true);
    try {
      const platformsToGenerate = selectedPlatform === 'all' 
        ? ['instagram', 'tiktok', 'facebook'] 
        : [selectedPlatform];

      await axios.post(`${API}/properties/${propertyId}/viral-content`, {
        platforms: platformsToGenerate
      });

      toast.success('New viral content generated!');
      fetchPropertyAndContent();
    } catch (error) {
      toast.error('Failed to generate content');
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const shareContent = async (platform) => {
    try {
      await axios.post(`${API}/properties/${propertyId}/share`, { platform });
      toast.success('Share tracked!');
    } catch (error) {
      console.error('Error tracking share:', error);
    }
  };

  const getViralScoreColor = (score) => {
    if (score >= 90) return 'viral-score-viral';
    if (score >= 75) return 'viral-score-high';
    if (score >= 50) return 'viral-score-medium';
    return 'viral-score-low';
  };

  const getViralScoreText = (score) => {
    if (score >= 90) return 'VIRAL POTENTIAL';
    if (score >= 75) return 'HIGH ENGAGEMENT';
    if (score >= 50) return 'GOOD POTENTIAL';
    return 'NEEDS IMPROVEMENT';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="spinner mb-4"></div>
          <p>Loading viral content...</p>
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <p>Property not found</p>
          <button onClick={() => navigate('/dashboard')} className="btn-viral mt-4">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const filteredContent = selectedPlatform === 'all' 
    ? viralContent 
    : viralContent.filter(content => content.platform === selectedPlatform);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-2xl hover:text-purple-300 transition-colors"
          >
            ←
          </button>
          <div className="flex-1">
            <motion.h1 
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              className="text-3xl font-bold mb-2"
            >
              Viral Content for {property.title}
            </motion.h1>
            <p className="text-purple-200">{property.address}</p>
          </div>
          <button
            onClick={() => navigate(`/analytics/${propertyId}`)}
            className="border border-white/30 rounded-lg px-4 py-2 hover:bg-white/10 transition-all"
          >
            View Analytics
          </button>
        </div>

        {/* Property Summary */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass rounded-xl p-6 mb-8"
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm opacity-80">Price</div>
              <div className="text-xl font-bold text-green-400">{property.price}</div>
            </div>
            <div>
              <div className="text-sm opacity-80">Type</div>
              <div className="text-xl font-bold">{property.property_type}</div>
            </div>
            <div>
              <div className="text-sm opacity-80">Size</div>
              <div className="text-xl font-bold">
                {property.bedrooms}BR / {property.bathrooms}BA
              </div>
            </div>
            <div>
              <div className="text-sm opacity-80">Area</div>
              <div className="text-xl font-bold">{property.square_feet} ft²</div>
            </div>
          </div>
        </motion.div>

        {/* Content Generation Controls */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-xl p-6 mb-8"
        >
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedPlatform('all')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  selectedPlatform === 'all' ? 'btn-viral' : 'bg-white/10 hover:bg-white/20'
                }`}
              >
                All Platforms
              </button>
              {platforms.map(platform => (
                <button
                  key={platform.id}
                  onClick={() => setSelectedPlatform(platform.id)}
                  className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
                    selectedPlatform === platform.id ? 'btn-viral' : 'bg-white/10 hover:bg-white/20'
                  }`}
                >
                  <span>{platform.icon}</span>
                  {platform.name}
                </button>
              ))}
            </div>
            <button
              onClick={generateContent}
              disabled={generating}
              className="btn-viral disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generating ? (
                <div className="flex items-center gap-2">
                  <div className="spinner"></div>
                  Generating...
                </div>
              ) : (
                'Generate New Content'
              )}
            </button>
          </div>
        </motion.div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredContent.length === 0 ? (
            <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="col-span-full glass rounded-xl p-12 text-center"
            >
              <div className="text-6xl mb-4">🚀</div>
              <h3 className="text-xl font-semibold mb-2">No content generated yet</h3>
              <p className="opacity-80 mb-6">Click "Generate New Content" to create viral content for this property</p>
              <button onClick={generateContent} className="btn-viral">
                Generate First Content
              </button>
            </motion.div>
          ) : (
            filteredContent.map((content, index) => {
              const platform = platforms.find(p => p.id === content.platform);
              return (
                <motion.div
                  key={content.id}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass rounded-xl p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{platform?.icon}</span>
                      <div>
                        <h3 className="font-semibold">{platform?.name}</h3>
                        <p className="text-sm opacity-60">
                          {new Date(content.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-semibold ${getViralScoreColor(content.viral_score)}`}>
                      {content.viral_score}/100 - {getViralScoreText(content.viral_score)}
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-4 mb-4 max-h-60 overflow-y-auto custom-scrollbar">
                    <pre className="whitespace-pre-wrap text-sm">{content.content}</pre>
                  </div>

                  {content.hashtags && content.hashtags.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm opacity-60 mb-2">Hashtags:</p>
                      <div className="flex flex-wrap gap-1">
                        {content.hashtags.slice(0, 10).map((tag, i) => (
                          <span key={i} className="text-xs bg-purple-500/30 px-2 py-1 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={() => copyToClipboard(content.content)}
                      className="flex-1 border border-white/30 rounded-lg py-2 px-4 hover:bg-white/10 transition-all text-sm"
                    >
                      📋 Copy
                    </button>
                    <button
                      onClick={() => shareContent(content.platform)}
                      className="flex-1 btn-viral py-2 px-4 text-sm"
                    >
                      📤 Share
                    </button>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default ViralContentGenerator;
