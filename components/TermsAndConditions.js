import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const TermsAndConditions = () => {
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
          <h1 className="text-3xl font-bold">Terms and Conditions</h1>
        </div>

        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass rounded-xl p-8 max-w-4xl mx-auto"
        >
          <div className="prose prose-invert max-w-none">
            <h2>Terms of Service</h2>
            <p><strong>Last updated:</strong> {new Date().toLocaleDateString()}</p>
            
            <h3>1. Acceptance of Terms</h3>
            <p>By accessing and using ListingSpark AI, you accept and agree to be bound by the terms and provision of this agreement.</p>
            
            <h3>2. Description of Service</h3>
            <p>ListingSpark AI provides AI-powered content generation services for real estate listings and social media marketing.</p>
            
            <h3>3. User Responsibilities</h3>
            <ul>
              <li>Provide accurate property information</li>
              <li>Use generated content responsibly</li>
              <li>Comply with social media platform guidelines</li>
              <li>Respect intellectual property rights</li>
            </ul>
            
            <h3>4. Service Availability</h3>
            <p>We strive to maintain service availability but cannot guarantee uninterrupted access.</p>
            
            <h3>5. Content Rights</h3>
            <p>Generated content is provided for your use. You retain rights to your property information and descriptions.</p>
            
            <h3>6. Privacy</h3>
            <p>Please review our Privacy Policy for information about how we collect and use your data.</p>
            
            <h3>7. Limitation of Liability</h3>
            <p>ListingSpark AI is not liable for any indirect, incidental, or consequential damages arising from use of our service.</p>
            
            <h3>8. Contact Information</h3>
            <p>For questions about these terms, contact us at info@launchlocal.com or call 661-932-0000.</p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default TermsAndConditions;
