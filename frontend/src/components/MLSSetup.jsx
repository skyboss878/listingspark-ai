import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import toast from 'react-hot-toast';

const MLSSetup = () => {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    provider: 'demo',
    account_name: '',
    client_id: '',
    client_secret: '',
    description: ''
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await api.get('/mls/accounts');
      setAccounts(response.data);
    } catch (error) {
      console.error('Error fetching MLS accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      toast.loading('Connecting to MLS...', { id: 'mls-connect' });
      
      const response = await api.post('/mls/accounts', formData);
      
      if (response.data.is_connected) {
        toast.success('✅ MLS account connected successfully!', { id: 'mls-connect' });
      } else {
        toast.success('MLS account added. Testing connection...', { id: 'mls-connect' });
      }
      
      setShowForm(false);
      fetchAccounts();
      setFormData({
        provider: 'demo',
        account_name: '',
        client_id: '',
        client_secret: '',
        description: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add MLS account', { id: 'mls-connect' });
    }
  };

  const testConnection = async (accountId) => {
    try {
      toast.loading('Testing connection...', { id: 'test' });
      const response = await api.post(`/mls/test/${accountId}`);
      
      if (response.data.connected) {
        toast.success('✅ Connection successful!', { id: 'test' });
      } else {
        toast.error('❌ Connection failed', { id: 'test' });
      }
      
      fetchAccounts();
    } catch (error) {
      toast.error('Connection test failed', { id: 'test' });
    }
  };

  const deleteAccount = async (accountId) => {
    if (!window.confirm('Are you sure you want to delete this MLS account?')) return;
    
    try {
      await api.delete(`/mls/accounts/${accountId}`);
      toast.success('MLS account deleted');
      fetchAccounts();
    } catch (error) {
      toast.error('Failed to delete account');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-12 h-12 border-4 border-purple-400 border-t-transparent rounded-full animate-spin mb-4 mx-auto"></div>
          <p>Loading MLS accounts...</p>
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
            <h1 className="text-3xl font-bold mb-2">MLS Integration</h1>
            <p className="text-purple-200">Connect your MLS accounts to publish listings</p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="border border-white/30 rounded-lg px-4 py-2 hover:bg-white/10 transition-all"
          >
            ← Back to Dashboard
          </button>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-500/20 border border-blue-500/30 rounded-xl p-6 mb-8">
          <div className="flex items-start gap-4">
            <div className="text-4xl">ℹ️</div>
            <div>
              <h3 className="font-bold text-lg mb-2">About MLS Integration</h3>
              <p className="text-blue-100 mb-2">
                Connect your MLS account to publish listings directly to the MLS, which automatically syndicates to:
              </p>
              <div className="flex flex-wrap gap-3 mt-3">
                <span className="bg-blue-600 px-3 py-1 rounded-full text-sm">Zillow</span>
                <span className="bg-blue-600 px-3 py-1 rounded-full text-sm">Realtor.com</span>
                <span className="bg-blue-600 px-3 py-1 rounded-full text-sm">Trulia</span>
                <span className="bg-blue-600 px-3 py-1 rounded-full text-sm">Homes.com</span>
              </div>
            </div>
          </div>
        </div>

        {/* Existing Accounts */}
        {accounts.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Connected Accounts</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {accounts.map((account) => (
                <motion.div
                  key={account.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-bold text-lg">{account.account_name}</h3>
                      <p className="text-sm text-purple-200 capitalize">{account.provider.replace('_', ' ')}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      account.is_connected 
                        ? 'bg-green-500 text-white' 
                        : 'bg-yellow-500 text-black'
                    }`}>
                      {account.is_connected ? '✓ Connected' : '○ Not Connected'}
                    </span>
                  </div>

                  {account.description && (
                    <p className="text-sm opacity-80 mb-4">{account.description}</p>
                  )}

                  {account.last_sync && (
                    <p className="text-xs opacity-70 mb-4">
                      Last sync: {new Date(account.last_sync).toLocaleString()}
                    </p>
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={() => testConnection(account.id)}
                      className="flex-1 bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-700 transition-all text-sm"
                    >
                      Test Connection
                    </button>
                    <button
                      onClick={() => deleteAccount(account.id)}
                      className="px-4 py-2 rounded-lg border border-red-500 text-red-400 hover:bg-red-500/20 transition-all text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Add New Account */}
        {!showForm ? (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowForm(true)}
            className="w-full bg-gradient-to-r from-purple-500 to-pink-500 py-4 rounded-xl font-semibold text-lg hover:shadow-lg transition-all"
          >
            + Add MLS Account
          </motion.button>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20"
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Add MLS Account</h2>
              <button
                onClick={() => setShowForm(false)}
                className="text-white/60 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block mb-2 text-sm font-medium">MLS Provider</label>
                <select
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-purple-400"
                  required
                >
                  <option value="demo">Demo (Testing)</option>
                  <option value="crmls">CRMLS (California)</option>
                  <option value="bright_mls">Bright MLS (Mid-Atlantic)</option>
                  <option value="rets_rabbit">RETS Rabbit (Universal)</option>
                  <option value="stellar_mls">Stellar MLS</option>
                </select>
              </div>

              <div>
                <label className="block mb-2 text-sm font-medium">Account Name</label>
                <input
                  type="text"
                  value={formData.account_name}
                  onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  placeholder="My MLS Account"
                  required
                />
              </div>

              {formData.provider !== 'demo' && (
                <>
                  <div>
                    <label className="block mb-2 text-sm font-medium">Client ID</label>
                    <input
                      type="text"
                      value={formData.client_id}
                      onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                      placeholder="Enter your MLS client ID"
                      required={formData.provider !== 'demo'}
                    />
                  </div>

                  <div>
                    <label className="block mb-2 text-sm font-medium">Client Secret</label>
                    <input
                      type="password"
                      value={formData.client_secret}
                      onChange={(e) => setFormData({ ...formData, client_secret: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                      placeholder="Enter your MLS client secret"
                      required={formData.provider !== 'demo'}
                    />
                  </div>
                </>
              )}

              {formData.provider === 'demo' && (
                <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-4">
                  <p className="text-sm text-yellow-100">
                    <strong>Demo Mode:</strong> You can test the platform without real MLS credentials. 
                    Publishing will be simulated but won't actually post to MLS.
                  </p>
                </div>
              )}

              <div>
                <label className="block mb-2 text-sm font-medium">Description (Optional)</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  placeholder="Notes about this MLS account"
                  rows="3"
                />
              </div>

              <div className="flex gap-4">
                <button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 py-3 rounded-lg font-semibold hover:shadow-lg transition-all"
                >
                  Add Account
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-6 py-3 rounded-lg border border-white/30 hover:bg-white/10 transition-all"
                >
                  Cancel
                </button>
              </div>
            </form>
          </motion.div>
        )}

        {/* Help Section */}
        <div className="mt-8 bg-purple-500/20 border border-purple-500/30 rounded-xl p-6">
          <h3 className="font-bold text-lg mb-3">📚 Need Help?</h3>
          <div className="space-y-2 text-sm text-purple-100">
            <p>• <strong>Demo Mode:</strong> Perfect for testing. No real MLS credentials needed.</p>
            <p>• <strong>Client ID & Secret:</strong> Obtain these from your MLS provider's API portal.</p>
            <p>• <strong>RESO Web API:</strong> Most modern MLS systems use the RESO standard.</p>
            <p>• <strong>Support:</strong> Contact your MLS provider for API access credentials.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLSSetup;
