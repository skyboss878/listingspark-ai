import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const PrivacyPolicy = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate('/')}
            className="text-2xl hover:text-purple-300 transition-colors"
          >
            ←
          </button>
          <h1 className="text-3xl font-bold">Privacy Policy</h1>
        </div>

        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass rounded-xl p-8 max-w-4xl mx-auto"
        >
          <div className="prose prose-invert max-w-none">
            <h2>Privacy Policy</h2>
            <p><strong>Last updated:</strong> {new Date().toLocaleDateString()}</p>
            
            <h3>1. Information We Collect</h3>
            <ul>
              <li><strong>Account Information:</strong> Name, email address</li>
              <li><strong>Property Data:</strong> Listings, descriptions, photos</li>
              <li><strong>Usage Data:</strong> How you interact with our service</li>
              <li><strong>Analytics:</strong> Performance metrics for generated content</li>
            </ul>
            
            <h3>2. How We Use Your Information</h3>
            <ul>
              <li>Provide and improve our AI content generation services</li>
              <li>Generate personalized viral content for your properties</li>
              <li>Analyze content performance and engagement</li>
              <li>Communicate service updates and support</li>
            </ul>
            
            <h3>3. Data Sharing</h3>
            <p>We do not sell your personal information. We may share data with:</p>
            <ul>
              <li>AI service providers for content generation</li>
              <li>Analytics services for performance tracking</li>
              <li>Payment processors for billing</li>
            </ul>
            
            <h3>4. Data Security</h3>
            <p>We implement industry-standard security measures to protect your data including encryption and secure storage.</p>
            
            <h3>5. Your Rights</h3>
            <ul>
              <li>Access your personal data</li>
              <li>Request data corrections</li>
              <li>Delete your account and data</li>
              <li>Export your property listings</li>
            </ul>
            
            <h3>6. Cookies</h3>
            <p>We use cookies to improve user experience and analyze usage patterns. You can control cookie settings in your browser.</p>
            
            <h3>7. Contact Us</h3>
            <p>For privacy questions or requests, contact us at:</p>
            <ul>
              <li>Email: info@launchlocal.com</li>
              <li>Phone: 661-932-0000</li>
            </ul>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
