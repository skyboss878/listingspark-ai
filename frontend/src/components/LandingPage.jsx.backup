import React, { useState, useContext } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import axios from 'axios';
import { UserContext } from '../App';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const LandingPage = () => {
  const [isSignupOpen, setIsSignupOpen] = useState(false);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  });
  const { login } = useContext(UserContext);
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_URL}/api/users`, {
        name: formData.name,
        email: formData.email,
      });

      const userData = response.data;
      login(userData);
      toast.success('Account created! Please select a plan to continue.');
      navigate('/pricing');
    } catch (error) {
      toast.error('Failed to create account. Please try again.');
      console.error('Signup error:', error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      // Add your login API call here
      const response = await axios.post(`${API_URL}/api/login`, {
        email: formData.email,
        password: formData.password
      });
      
      const userData = response.data;
      login(userData);
      
      // Check if user has active subscription
      if (userData.subscription && userData.subscription.active) {
        navigate('/dashboard');
      } else {
        toast.info('Please select a subscription plan');
        navigate('/pricing');
      }
    } catch (error) {
      toast.error('Login failed. Please check your credentials.');
      console.error('Login error:', error);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <motion.header
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="relative z-50 px-6 py-4"
      >
        <nav className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2 cursor-pointer" onClick={() => navigate('/')}>
            <span className="text-3xl">⚡</span>
            <span className="text-2xl font-bold text-white">ListingSpark AI</span>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsLoginOpen(true)}
              className="text-white hover:text-blue-200 transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => setIsSignupOpen(true)}
              className="bg-white text-purple-900 px-6 py-2 rounded-full font-semibold hover:bg-blue-50 transition-all transform hover:scale-105"
            >
              Get Started
            </button>
          </div>
        </nav>
      </motion.header>

      {/* Hero Section */}
      <section className="relative px-6 py-20">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-6xl md:text-8xl font-black text-white mb-8 leading-tight">
              Turn Boring Listings Into
              <span className="bg-gradient-to-r from-yellow-400 to-pink-400 bg-clip-text text-transparent">
                {' '}VIRAL GOLD
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-blue-100 mb-12 max-w-4xl mx-auto leading-relaxed">
              The AI-powered platform that transforms your property listings into scroll-stopping,
              share-worthy content that sells houses faster than traditional marketing.
            </p>
          </motion.div>

          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="flex flex-col sm:flex-row gap-6 justify-center items-center"
          >
            <button
              onClick={() => setIsSignupOpen(true)}
              className="bg-gradient-to-r from-pink-500 to-yellow-500 text-white text-xl font-bold px-12 py-4 rounded-full hover:from-pink-600 hover:to-yellow-600 transition-all transform hover:scale-105 shadow-2xl"
            >
              Get Started Now
            </button>
            <button className="text-white text-lg font-semibold flex items-center space-x-2 hover:text-blue-200 transition-colors">
              <span>Watch Demo</span>
              <span>▶️</span>
            </button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            className="grid grid-cols-3 gap-8 mt-20 max-w-3xl mx-auto"
          >
            <div className="text-center">
              <div className="text-4xl font-bold text-yellow-400">500%</div>
              <div className="text-blue-200">More Engagement</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-pink-400">10x</div>
              <div className="text-blue-200">Faster Sales</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-400">95%</div>
              <div className="text-blue-200">Client Satisfaction</div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white/5 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-bold text-white mb-6">
              Everything You Need to Go Viral
            </h2>
            <p className="text-xl text-blue-100 max-w-3xl mx-auto">
              Our AI analyzes millions of viral posts to create content that stops the scroll and starts conversations.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: '🤖',
                title: 'AI Content Generation',
                description: 'Advanced AI creates platform-specific content that\'s proven to drive engagement and shares.'
              },
              {
                icon: '📊',
                title: 'Viral Analytics',
                description: 'Real-time tracking of engagement, shares, and viral potential across all social platforms.'
              },
              {
                icon: '🎥',
                title: 'Virtual Tours',
                description: 'Automated virtual tour creation with AI-generated narration and trending music.'
              },
              {
                icon: '📱',
                title: 'Multi-Platform Publishing',
                description: 'Optimized content for Instagram, TikTok, Facebook, Twitter, and LinkedIn in one click.'
              },
              {
                icon: '🎯',
                title: 'Trend Integration',
                description: 'Automatically incorporates trending hashtags, sounds, and formats for maximum reach.'
              },
              {
                icon: '⚡',
                title: 'Instant Results',
                description: 'Generate months of viral-ready content in minutes, not days.'
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ y: 50, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-8 text-center hover:bg-white/20 transition-all transform hover:scale-105"
              >
                <div className="text-5xl mb-4">{feature.icon}</div>
                <h3 className="text-2xl font-bold text-white mb-4">{feature.title}</h3>
                <p className="text-blue-100">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-r from-purple-600 to-pink-600">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
          >
            <h2 className="text-5xl font-bold text-white mb-6">
              Ready to Transform Your Real Estate Game?
            </h2>
            <p className="text-xl text-pink-100 mb-12">
              Join thousands of realtors who've already discovered the power of viral marketing.
            </p>
            <button
              onClick={() => navigate('/pricing')}
              className="bg-white text-purple-600 text-2xl font-bold px-16 py-6 rounded-full hover:bg-gray-100 transition-all transform hover:scale-105 shadow-2xl"
            >
              View Pricing Plans
            </button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-black/20">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-8">
            <span className="text-3xl">⚡</span>
            <span className="text-2xl font-bold text-white">ListingSpark AI</span>
          </div>
          <div className="flex justify-center space-x-8 mb-8">
            <a href="/terms" className="text-blue-200 hover:text-white transition-colors">Terms</a>
            <a href="/privacy" className="text-blue-200 hover:text-white transition-colors">Privacy</a>
            <span className="text-blue-200">Contact: info@listingspark.ai</span>
          </div>
          <p className="text-blue-300">© 2024 ListingSpark AI. All rights reserved.</p>
        </div>
      </footer>

      {/* Signup Modal */}
      {isSignupOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setIsSignupOpen(false)}
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-3xl p-8 max-w-md w-full relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setIsSignupOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl"
            >
              ✕
            </button>

            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Create Your Account</h2>
              <p className="text-gray-600">Get started with ListingSpark AI</p>
            </div>

            <form onSubmit={handleSignup} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Enter your full name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Enter your email"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Create a password"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-4 rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all"
              >
                Create Account
              </button>
            </form>

            <p className="text-center text-gray-600 mt-4">
              Already have an account?{' '}
              <button
                onClick={() => {
                  setIsSignupOpen(false);
                  setIsLoginOpen(true);
                }}
                className="text-purple-600 hover:text-purple-700 font-semibold"
              >
                Login
              </button>
            </p>
          </motion.div>
        </motion.div>
      )}

      {/* Login Modal */}
      {isLoginOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setIsLoginOpen(false)}
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-3xl p-8 max-w-md w-full relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setIsLoginOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl"
            >
              ✕
            </button>

            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h2>
              <p className="text-gray-600">Login to your account</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Enter your email"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Enter your password"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-4 rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all"
              >
                Login
              </button>
            </form>

            <p className="text-center text-gray-600 mt-4">
              Don't have an account?{' '}
              <button
                onClick={() => {
                  setIsLoginOpen(false);
                  setIsSignupOpen(true);
                }}
                className="text-purple-600 hover:text-purple-700 font-semibold"
              >
                Sign up
              </button>
            </p>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};

export default LandingPage;
