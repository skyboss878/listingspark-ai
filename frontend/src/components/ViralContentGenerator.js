import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../utils/api';
import toast from 'react-hot-toast';

const ViralContentGenerator = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [content, setContent] = useState([]);
  const [selectedPlatform, setSelectedPlatform] = useState('instagram');

  const platforms = [
    { id: 'instagram', name: 'Instagram', icon: '📸', color: 'from-pink-500 to-purple-500' },
    { id: 'tiktok', name: 'TikTok', icon: '🎵', color: 'from-cyan-500 to-blue-500' },
    { id: 'facebook', name: 'Facebook', icon: '👥', color: 'from-blue-500 to-indigo-500' }
  ];

  useEffect(() => {
    loadContent();
  }, [propertyId, loadContent]);

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
        {selectedContent ? (
          <motion.div
            key={selectedPlatform}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-8"
          >
            {/* Content Preview */}
            <div className="glass rounded-xl p-8">
              <div className="flex justify-between items-start mb-6">
                <h2 className="text-2xl font-bold">Content Preview</h2>
                {selectedContent.ai_generated && (
                  <span className="px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full text-xs font-semibold">
                    AI Generated
                  </span>
                )}
              </div>

              <div className="bg-black/30 rounded-lg p-6 mb-6 min-h-[300px] max-h-[500px] overflow-y-auto">
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                  {selectedContent.content}
                </pre>
              </div>

              <button
                onClick={() => copyToClipboard(selectedContent.content)}
                className="w-full btn-viral py-3"
              >
                📋 Copy to Clipboard
              </button>
            </div>

            {/* Analytics & Info */}
            <div className="space-y-6">
              {/* Viral Score */}
              <div className="glass rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-4">Viral Score</h3>
                <div className="relative">
                  <div className="flex items-end justify-center mb-4">
                    <div className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500">
                      {selectedContent.viral_score}
                    </div>
                    <div className="text-2xl text-purple-200 mb-2">/100</div>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-4 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${selectedContent.viral_score}%` }}
                      transition={{ duration: 1, delay: 0.5 }}
                      className="h-full bg-gradient-to-r from-green-400 via-blue-500 to-purple-500"
                    />
                  </div>
                  <div className="flex justify-between text-xs text-purple-200 mt-2">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                    <span>Viral</span>
                  </div>
                </div>
              </div>

              {/* Hashtags */}
              <div className="glass rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-4">Hashtags</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedContent.hashtags.map((tag, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-purple-500/20 rounded-full text-sm border border-purple-400/30"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <button
                  onClick={() => copyToClipboard(selectedContent.hashtags.join(' '))}
                  className="mt-4 w-full px-4 py-2 border border-white/30 rounded-lg hover:bg-white/10 transition-all text-sm"
                >
                  Copy All Hashtags
                </button>
              </div>

              {/* Stats */}
              <div className="glass rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-4">Content Stats</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-purple-200">Character Count</span>
                    <span className="font-semibold">{selectedContent.content.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-200">Word Count</span>
                    <span className="font-semibold">
                      {selectedContent.content.split(/\s+/).length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-200">Hashtag Count</span>
                    <span className="font-semibold">{selectedContent.hashtags.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-200">Platform</span>
                    <span className="font-semibold capitalize">{selectedContent.platform}</span>
                  </div>
                </div>
              </div>

              {/* Regenerate Button */}
              <button
                onClick={generateContent}
                disabled={generating}
                className="w-full px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl font-semibold hover:shadow-lg hover:shadow-purple-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generating ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Regenerating...
                  </span>
                ) : (
                  '🔄 Regenerate All Content'
                )}
              </button>
            </div>
          </motion.div>
        ) : (
          <div className="glass rounded-xl p-12 text-center">
            <div className="text-6xl mb-4">🎨</div>
            <h3 className="text-2xl font-semibold mb-4">No Content Yet</h3>
            <p className="text-purple-200 mb-6">
              Generate viral content for this property
            </p>
            <button
              onClick={generateContent}
              disabled={generating}
              className="btn-viral px-8 py-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generating ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Generating...
                </span>
              ) : (
                'Generate Viral Content'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ViralContentGenerator;
