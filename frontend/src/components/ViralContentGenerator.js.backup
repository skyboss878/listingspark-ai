import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import api from '../utils/api';

const platforms = [
  { id: 'instagram', name: 'Instagram', icon: '📸' },
  { id: 'facebook', name: 'Facebook', icon: '👥' },
  { id: 'twitter', name: 'Twitter', icon: '🐦' },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
  { id: 'tiktok', name: 'TikTok', icon: '🎵' },
];

  const ViralContentGenerator = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [content, setContent] = useState([]);
  const [selectedPlatform, setSelectedPlatform] = useState('instagram');
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
 const voiceOptions = [
  { id: 'professional_female', name: 'Professional Female (Luxury)', icon: '👩‍💼' },
  { id: 'professional_male', name: 'Professional Male (Commercial)', icon: '👨‍💼' },
  { id: 'friendly_female', name: 'Friendly Female (Family)', icon: '👩' },
  { id: 'luxury_male', name: 'Luxury Male (High-End)', icon: '🎩' }
];

  // Define generateContent FIRST (before loadContent that depends on it)
  const generateContent = useCallback(async () => {
    try {
      setGenerating(true);
      toast.loading('Generating viral content with AI...', { id: 'generate' });

      const result = await api.viralContent.generate(propertyId);

      setContent(result.content);
      toast.success('Viral content generated!', { id: 'generate' });
    } catch (error) {
      console.error('Error generating content:', error);
      toast.error('Failed to generate content', { id: 'generate' });
    } finally {
      setGenerating(false);
    }
  }, [propertyId]);

  // Define loadContent SECOND (after generateContent)
  const loadContent = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.viralContent.get(propertyId);

      if (data.length === 0) {
        // No content yet, generate it
        await generateContent();
      } else {
        setContent(data);
      }
    } catch (error) {
      console.error('Error loading content:', error);
      toast.error('Failed to load content');
    } finally {
      setLoading(false);
    }
  }, [propertyId, generateContent]);

  // UseEffect THIRD (after both functions are defined)
  useEffect(() => {
    loadContent();
  }, [loadContent]);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const selectedContent = content.find(c => c.platform === selectedPlatform);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="text-white text-center">
        <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p>Loading content...</p>
  
      </div>
    </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white py-12">
      <div className="container mx-auto px-6 max-w-6xl">
        {/* Header */}
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
          <h1 className="text-4xl font-bold mb-2">Viral Content Generator</h1>
          <p className="text-purple-200">
            AI-powered content optimized for each platform
          </p>
        </motion.div>

        {/* Platform Selector */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <div className="flex gap-4">
            {platforms.map((platform) => (
              <button
                key={platform.id}
                onClick={() => setSelectedPlatform(platform.id)}
                className={`
                  flex-1 p-6 rounded-xl border-2 transition-all
                  ${selectedPlatform === platform.id
                    ? 'border-white bg-white/10'
                    : 'border-white/20 hover:border-white/40'
                  }
                `}
              >
                <div className="text-4xl mb-2">{platform.icon}</div>
                <div className="font-semibold">{platform.name}</div>
              </button>
            ))}
          </div>
        </motion.div>

        {/* Content Display */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20"
        >
          {selectedContent ? (
            <div>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold mb-2">
                    {platforms.find(p => p.id === selectedPlatform)?.name} Post
                  </h2>
                  <p className="text-purple-200">
                    Optimized for maximum engagement
                  </p>
                </div>
                <button
                  onClick={() => copyToClipboard(selectedContent.content)}
                  className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
                >
                  📋 Copy
                </button>
              </div>

              <div className="bg-white/5 rounded-xl p-6 mb-6">
                <pre className="whitespace-pre-wrap font-sans">
                  {selectedContent.content}
                </pre>
              </div>

              {selectedContent.hashtags && (
                <div className="mb-6">
                  <h3 className="font-semibold mb-2">Hashtags</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedContent.hashtags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-white/10 rounded-full text-sm"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedContent.tips && (
                <div>
                  <h3 className="font-semibold mb-2">Pro Tips</h3>
                  <ul className="space-y-2">
                    {selectedContent.tips.map((tip, index) => (
                      <li key={index} className="flex gap-2">
                        <span>💡</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-xl mb-4">No content generated yet</p>
              <button
                onClick={generateContent}
                disabled={generating}
                className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50"
              >
                {generating ? 'Generating...' : '✨ Generate Content'}
              </button>
            </div>
          )}
        </motion.div>

        {/* Regenerate Button */}
        {selectedContent && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="mt-6 text-center"
          >
            <button
              onClick={generateContent}
              disabled={generating}
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50"
            >
              {generating ? 'Regenerating...' : '🔄 Regenerate All Content'}
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default ViralContentGenerator;
