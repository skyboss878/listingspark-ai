import React, { useState, useContext } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { UserContext } from '../App';
import api from '../utils/api';
import toast from 'react-hot-toast';

const PropertyCreator = () => {
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    address: '',
    price: '',
    property_type: 'house',
    bedrooms: '',
    bathrooms: '',
    square_feet: '',
    features: []
  });

  const propertyTypes = [
    { value: 'house', label: 'House', icon: '🏠' },
    { value: 'apartment', label: 'Apartment', icon: '🏢' },
    { value: 'condo', label: 'Condo', icon: '🏘️' },
    { value: 'townhouse', label: 'Townhouse', icon: '🏡' },
    { value: 'land', label: 'Land', icon: '🌳' }
  ];

  const availableFeatures = [
    'Swimming Pool', 'Garage', 'Garden', 'Fireplace', 'Gym',
    'Smart Home', 'Solar Panels', 'Hardwood Floors', 'Updated Kitchen',
    'Walk-in Closet', 'Balcony', 'Home Office', 'Security System'
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const toggleFeature = (feature) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.includes(feature)
        ? prev.features.filter(f => f !== feature)
        : [...prev.features, feature]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.address || !formData.price) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);

    try {
      const propertyData = {
        title: formData.title,
        description: formData.description,
        address: formData.address,
        price: formData.price,
        property_type: formData.property_type,
        bedrooms: formData.bedrooms ? parseInt(formData.bedrooms) : null,
        bathrooms: formData.bathrooms ? parseFloat(formData.bathrooms) : null,
        square_feet: formData.square_feet ? parseInt(formData.square_feet) : null,
        features: formData.features
      };

      const result = await api.properties.create(user.id, propertyData);
      
      toast.success('Property created successfully!');
      
      // Ask if they want to add a 360 tour
      setTimeout(() => {
        if (window.confirm('Property created! Would you like to add a 360° virtual tour?')) {
          navigate(`/upload-tour/${result.id}`);
        } else {
          navigate('/dashboard');
        }
      }, 500);

    } catch (error) {
      console.error('Error creating property:', error);
      toast.error('Failed to create property');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white py-12">
      <div className="container mx-auto px-6 max-w-4xl">
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
          <h1 className="text-4xl font-bold mb-2">Create New Property</h1>
          <p className="text-purple-200">
            Fill in the details to create your property listing
          </p>
        </motion.div>

        {/* Form */}
        <motion.form
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          onSubmit={handleSubmit}
          className="glass rounded-xl p-8 space-y-6"
        >
          {/* Basic Info */}
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">Basic Information</h2>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Property Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="e.g., Modern 3BR Home in Downtown"
                className="w-full px-4 py-3 bg-white/10 rounded-lg border border-white/20 focus:border-purple-400 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Address *
              </label>
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="e.g., 123 Main St, San Francisco, CA 94102"
                className="w-full px-4 py-3 bg-white/10 rounded-lg border border-white/20 focus:border-purple-400 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Price *
              </label>
              <input
                type="text"
                name="price"
                value={formData.price}
                onChange={handleChange}
                placeholder="e.g., $850,000"
                className="w-full px-4 py-3 bg-white/10 rounded-lg border border-white/20 focus:border-purple-400 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Describe the property's best features..."
                rows="4"
                className="w-full px-4 py-3 bg-white/10 rounded-lg border border-white/20 focus:border-purple-400 focus:outline-none resize-none"
              />
            </div>
          </div>

          {/* Property Type */}
          <div>
            <label className="block text-sm font-medium mb-3">
              Property Type
            </label>
            <div className="grid grid-cols-5 gap-3">
              {propertyTypes.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, property_type: type.value }))}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    formData.property_type === type.value
                      ? 'border-purple-400 bg-purple-500/20'
                      : 'border-white/20 hover:border-white/40'
                  }`}
                >
                  <div className="text-3xl mb-2">{type.icon}</div>
                  <div className="text-sm">{type.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Details */}
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">Property Details</h2>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Bedrooms
                </label>
                <input
                  type="number"
                  name="bedrooms"
                  value={formData.bedrooms}
                  onChange={handleChange}
                  min="0"
                  placeholder="3"
                  className="w-full px-4 py-3 bg-white/10 rounded-lg border border-white/20 focus:border-purple-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Bathrooms
                </label>
                <input
                  type="number"
                  name="bathrooms"
                  value={formData.bathrooms}
                  onChange={handleChange}
                  min="0"
                  step="0.5"
                  placeholder="2.5"
                  className="w-full px-4 py-3 bg-white/10 rounded-lg border border-white/20 focus:border-purple-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Square Feet
                </label>
                <input
                  type="number"
                  name="square_feet"
                  value={formData.square_feet}
                  onChange={handleChange}
                  min="0"
                  placeholder="2000"
                  className="w-full px-4 py-3 bg-white/10 rounded-lg border border-white/20 focus:border-purple-400 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Features */}
          <div>
            <label className="block text-sm font-medium mb-3">
              Features
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {availableFeatures.map((feature) => (
                <button
                  key={feature}
                  type="button"
                  onClick={() => toggleFeature(feature)}
                  className={`px-4 py-2 rounded-lg border-2 text-sm transition-all ${
                    formData.features.includes(feature)
                      ? 'border-purple-400 bg-purple-500/20'
                      : 'border-white/20 hover:border-white/40'
                  }`}
                >
                  {formData.features.includes(feature) && '✓ '}
                  {feature}
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <div className="flex gap-4 pt-6">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="flex-1 px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 btn-viral py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating...
                </span>
              ) : (
                'Create Property'
              )}
            </button>
          </div>
        </motion.form>
      </div>
    </div>
  );
};

export default PropertyCreator;
