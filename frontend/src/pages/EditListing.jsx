import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import api from '../api';
import toast from 'react-hot-toast';

const EditListing = () => {
  const { listingId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    property_type: 'single_family',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    price: '',
    bedrooms: '',
    bathrooms: '',
    square_feet: '',
    lot_size: '',
    year_built: '',
    description: '',
    features: [],
    office_spaces: '',
    parking_spaces: '',
    loading_docks: '',
    zoning: '',
    topography: '',
    utilities: ''
  });

  useEffect(() => {
    fetchListing();
  }, [listingId]);

  const fetchListing = async () => {
    try {
      const response = await api.get(`/listings/${listingId}`);
      const listing = response.data;
      setFormData({
        property_type: listing.property_type || 'single_family',
        address: listing.address || '',
        city: listing.city || '',
        state: listing.state || '',
        zip_code: listing.zip_code || '',
        price: listing.price || '',
        bedrooms: listing.bedrooms || '',
        bathrooms: listing.bathrooms || '',
        square_feet: listing.square_feet || '',
        lot_size: listing.lot_size || '',
        year_built: listing.year_built || '',
        description: listing.description || '',
        features: listing.features || [],
        office_spaces: listing.office_spaces || '',
        parking_spaces: listing.parking_spaces || '',
        loading_docks: listing.loading_docks || '',
        zoning: listing.zoning || '',
        topography: listing.topography || '',
        utilities: listing.utilities || ''
      });
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load listing');
      navigate('/dashboard');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      toast.loading('Updating listing...', { id: 'update' });
      
      const payload = {
        ...formData,
        price: parseFloat(formData.price),
        bedrooms: formData.bedrooms ? parseInt(formData.bedrooms) : null,
        bathrooms: formData.bathrooms ? parseFloat(formData.bathrooms) : null,
        square_feet: parseInt(formData.square_feet),
        lot_size: formData.lot_size ? parseFloat(formData.lot_size) : null,
        year_built: formData.year_built ? parseInt(formData.year_built) : null,
        office_spaces: formData.office_spaces ? parseInt(formData.office_spaces) : null,
        parking_spaces: formData.parking_spaces ? parseInt(formData.parking_spaces) : null,
        loading_docks: formData.loading_docks ? parseInt(formData.loading_docks) : null
      };
      
      await api.put(`/listings/${listingId}`, payload);
      
      toast.success('✅ Listing updated!', { id: 'update' });
      navigate('/dashboard');
    } catch (error) {
      toast.error('Failed to update listing', { id: 'update' });
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-400 border-t-transparent rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-xl">Loading listing...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        <button
          onClick={() => navigate('/dashboard')}
          className="text-white hover:text-purple-300 transition-colors mb-6"
        >
          ← Back to Dashboard
        </button>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20"
        >
          <h1 className="text-3xl font-bold mb-6">✏️ Edit Listing</h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Property Type */}
            <div>
              <label className="block mb-2 text-sm font-medium">Property Type</label>
              <select
                name="property_type"
                value={formData.property_type}
                onChange={handleInputChange}
                className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:border-purple-400"
                required
              >
                <option value="single_family">Single Family Home</option>
                <option value="condo">Condo</option>
                <option value="townhouse">Townhouse</option>
                <option value="multi_family">Multi-Family</option>
                <option value="commercial">Commercial</option>
                <option value="land">Land</option>
              </select>
            </div>

            {/* Address Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block mb-2 text-sm font-medium">Address</label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  required
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium">City</label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  required
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium">State</label>
                <input
                  type="text"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  required
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium">ZIP Code</label>
                <input
                  type="text"
                  name="zip_code"
                  value={formData.zip_code}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  required
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium">Price</label>
                <input
                  type="number"
                  name="price"
                  value={formData.price}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  required
                />
              </div>
            </div>

            {/* Residential Fields */}
            {!['commercial', 'land'].includes(formData.property_type) && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block mb-2 text-sm font-medium">Bedrooms</label>
                  <input
                    type="number"
                    name="bedrooms"
                    value={formData.bedrooms}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  />
                </div>
                <div>
                  <label className="block mb-2 text-sm font-medium">Bathrooms</label>
                  <input
                    type="number"
                    step="0.5"
                    name="bathrooms"
                    value={formData.bathrooms}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  />
                </div>
              </div>
            )}

            {/* Commercial Fields */}
            {formData.property_type === 'commercial' && (
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block mb-2 text-sm font-medium">Office Spaces</label>
                  <input
                    type="number"
                    name="office_spaces"
                    value={formData.office_spaces}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  />
                </div>
                <div>
                  <label className="block mb-2 text-sm font-medium">Parking Spaces</label>
                  <input
                    type="number"
                    name="parking_spaces"
                    value={formData.parking_spaces}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  />
                </div>
                <div>
                  <label className="block mb-2 text-sm font-medium">Loading Docks</label>
                  <input
                    type="number"
                    name="loading_docks"
                    value={formData.loading_docks}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  />
                </div>
              </div>
            )}

            {/* Land Fields */}
            {formData.property_type === 'land' && (
              <div className="space-y-4">
                <div>
                  <label className="block mb-2 text-sm font-medium">Zoning</label>
                  <input
                    type="text"
                    name="zoning"
                    value={formData.zoning}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  />
                </div>
                <div>
                  <label className="block mb-2 text-sm font-medium">Topography</label>
                  <input
                    type="text"
                    name="topography"
                    value={formData.topography}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  />
                </div>
                <div>
                  <label className="block mb-2 text-sm font-medium">Utilities</label>
                  <input
                    type="text"
                    name="utilities"
                    value={formData.utilities}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  />
                </div>
              </div>
            )}

            {/* Common Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block mb-2 text-sm font-medium">Square Feet</label>
                <input
                  type="number"
                  name="square_feet"
                  value={formData.square_feet}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  required
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium">Lot Size (acres)</label>
                <input
                  type="number"
                  step="0.01"
                  name="lot_size"
                  value={formData.lot_size}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                />
              </div>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium">Year Built</label>
              <input
                type="number"
                name="year_built"
                value={formData.year_built}
                onChange={handleInputChange}
                className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium">Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                rows="4"
              />
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 px-8 py-4 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50"
              >
                {saving ? '💾 Saving...' : '💾 Save Changes'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="px-8 py-4 bg-gray-600 rounded-lg hover:bg-gray-700 transition-all"
              >
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  );
};

export default EditListing;
