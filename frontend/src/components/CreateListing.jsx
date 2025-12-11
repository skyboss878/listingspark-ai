import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import toast from 'react-hot-toast';

const CreateListing = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [uploading, setUploading] = useState(false);
  const [customFieldName, setCustomFieldName] = useState('');
  const [customFieldValue, setCustomFieldValue] = useState('');
  const [customFields, setCustomFields] = useState({});
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
    images: [],
    // Commercial specific
    office_spaces: '',
    parking_spaces: '',
    loading_docks: '',
    // Land specific
    zoning: '',
    topography: '',
    utilities: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleFeatureAdd = (feature) => {
    if (feature && !formData.features.includes(feature)) {
      setFormData({ ...formData, features: [...formData.features, feature] });
    }
  };

  const handleFeatureRemove = (feature) => {
    setFormData({
      ...formData,
      features: formData.features.filter(f => f !== feature)
    });
  };

  const handleAddCustomField = () => {
    if (customFieldName && customFieldValue) {
      setCustomFields({
        ...customFields,
        [customFieldName]: customFieldValue
      });
      setCustomFieldName('');
      setCustomFieldValue('');
      toast.success(`Custom field "${customFieldName}" added!`);
    }
  };

  const handleRemoveCustomField = (fieldName) => {
    const newFields = { ...customFields };
    delete newFields[fieldName];
    setCustomFields(newFields);
  };

  // eslint-disable-next-line no-unused-vars
  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploading(true);
    const formDataObj = new FormData();
    files.forEach(file => formDataObj.append('files', file));

    try {
      const response = await api.post('/upload/images', formDataObj, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const imageUrls = response.data.files.map(f => f.url);
      setFormData({ ...formData, images: [...formData.images, ...imageUrls] });
      toast.success(`${files.length} images uploaded!`);
    } catch (error) {
      toast.error('Failed to upload images');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      toast.loading('Creating listing...', { id: 'create' });
      
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
        loading_docks: formData.loading_docks ? parseInt(formData.loading_docks) : null,
        custom_fields: customFields
      };
      
      await api.post('/listings', payload);
      
      toast.success('✅ Listing created!', { id: 'create' });
      navigate(`/dashboard`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create listing', { id: 'create' });
    }
  };

  const commonFeatures = [
    'Pool', 'Garage', 'Fireplace', 'Updated Kitchen', 'Hardwood Floors',
    'Central AC', 'Walk-in Closet', 'Patio', 'Balcony', 'Garden',
    'Smart Home', 'Solar Panels', 'Security System', 'Gym', 'Home Office'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Create New Listing</h1>
            <p className="text-purple-200">Add property details to get started</p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="border border-white/30 rounded-lg px-4 py-2 hover:bg-white/10 transition-all"
          >
            ← Cancel
          </button>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-between mb-8">
          {[
            { num: 1, label: 'Basic Info' },
            { num: 2, label: 'Details' },
            { num: 3, label: 'Features & Images' }
          ].map((s) => (
            <div key={s.num} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                step >= s.num ? 'bg-purple-500' : 'bg-white/10'
              }`}>
                {s.num}
              </div>
              <span className="ml-2 text-sm">{s.label}</span>
              {s.num < 3 && <div className="w-16 h-0.5 bg-white/20 mx-4" />}
            </div>
          ))}
        </div>

        {/* Form */}
        <motion.form
          key={step}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          onSubmit={handleSubmit}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20"
        >
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-2xl font-bold mb-6">Basic Information</h2>
              
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
                  <option value="land">Land</option>
                  <option value="commercial">Commercial</option>
                </select>
              </div>

              <div>
                <label className="block mb-2 text-sm font-medium">Address</label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  placeholder="123 Main Street"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block mb-2 text-sm font-medium">City</label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                    placeholder="Los Angeles"
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
                    placeholder="CA"
                    required
                    maxLength="2"
                  />
                </div>
              </div>

              <div>
                <label className="block mb-2 text-sm font-medium">ZIP Code</label>
                <input
                  type="text"
                  name="zip_code"
                  value={formData.zip_code}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  placeholder="90001"
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
                  placeholder="750000"
                  required
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-2xl font-bold mb-6">
                {formData.property_type === 'commercial' ? 'Commercial' : 
                 formData.property_type === 'land' ? 'Land' : 'Residential'} Property Details
              </h2>
              
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
                      placeholder="4"
                      required
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
                      placeholder="2.5"
                      required
                    />
                  </div>
                </div>
              )}

              {/* Commercial Fields */}
              {formData.property_type === 'commercial' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block mb-2 text-sm font-medium">Office Spaces</label>
                      <input
                        type="number"
                        name="office_spaces"
                        value={formData.office_spaces}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                        placeholder="10"
                        required
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
                        placeholder="50"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block mb-2 text-sm font-medium">Loading Docks (optional)</label>
                    <input
                      type="number"
                      name="loading_docks"
                      value={formData.loading_docks}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                      placeholder="2"
                    />
                  </div>
                </>
              )}

              {/* Land Fields */}
              {formData.property_type === 'land' && (
                <>
                  <div>
                    <label className="block mb-2 text-sm font-medium">Zoning</label>
                    <input
                      type="text"
                      name="zoning"
                      value={formData.zoning}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                      placeholder="Residential, Commercial, Agricultural..."
                      required
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
                      placeholder="Flat, Rolling, Hillside..."
                      required
                    />
                  </div>

                  <div>
                    <label className="block mb-2 text-sm font-medium">Utilities Available</label>
                    <input
                      type="text"
                      name="utilities"
                      value={formData.utilities}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                      placeholder="Water, Electric, Gas, Sewer..."
                      required
                    />
                  </div>
                </>
              )}

              {/* Common Fields */}
              <div>
                <label className="block mb-2 text-sm font-medium">
                  {formData.property_type === 'land' ? 'Land Area' : 'Square Feet'}
                </label>
                <input
                  type="number"
                  name="square_feet"
                  value={formData.square_feet}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  placeholder={formData.property_type === 'land' ? "43560 (1 acre)" : "2500"}
                  required
                />
              </div>

              {formData.property_type !== 'land' && (
                <div>
                  <label className="block mb-2 text-sm font-medium">Lot Size (acres, optional)</label>
                  <input
                    type="number"
                    step="0.01"
                    name="lot_size"
                    value={formData.lot_size}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                    placeholder="0.25"
                  />
                </div>
              )}

              <div>
                <label className="block mb-2 text-sm font-medium">Year Built (optional)</label>
                <input
                  type="number"
                  name="year_built"
                  value={formData.year_built}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  placeholder="2020"
                />
              </div>

              {/* Custom Fields Section */}
              <div className="border-t border-white/20 pt-4 mt-6">
                <h3 className="text-lg font-semibold mb-4">📝 Custom Fields (Optional)</h3>
                <p className="text-sm text-purple-200 mb-4">Add custom property details like "Cellar", "Wine Room", "Home Theater", etc.</p>
                
                {Object.keys(customFields).length > 0 && (
                  <div className="mb-4 space-y-2">
                    {Object.entries(customFields).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between bg-purple-500/20 rounded-lg px-4 py-2">
                        <div>
                          <span className="font-semibold">{key}:</span> {value}
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveCustomField(key)}
                          className="text-red-400 hover:text-red-300"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 mb-2">
                  <input
                    type="text"
                    value={customFieldName}
                    onChange={(e) => setCustomFieldName(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                    placeholder="Field name (e.g., Cellar)"
                  />
                  <input
                    type="text"
                    value={customFieldValue}
                    onChange={(e) => setCustomFieldValue(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                    placeholder="Value (e.g., Yes, 500 sq ft)"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleAddCustomField}
                  className="w-full py-3 bg-purple-600/50 rounded-lg hover:bg-purple-600 transition-colors"
                >
                  + Add Custom Field
                </button>
              </div>

              <div>
                <label className="block mb-2 text-sm font-medium">Description (optional)</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:border-purple-400"
                  placeholder="Describe the property... (AI will enhance this later)"
                  rows="4"
                />
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold mb-6">Features & Images</h2>
              
              <div>
                <label className="block mb-3 text-sm font-medium">Property Features</label>
                <div className="flex flex-wrap gap-2 mb-4">
                  {commonFeatures.map((feature) => (
                    <button
                      key={feature}
                      type="button"
                      onClick={() => handleFeatureAdd(feature)}
                      className={`px-4 py-2 rounded-lg text-sm transition-all ${
                        formData.features.includes(feature)
                          ? 'bg-purple-500 text-white'
                          : 'bg-white/10 border border-white/20 hover:bg-white/20'
                      }`}
                    >
                      {feature}
                    </button>
                  ))}
                </div>
                {formData.features.length > 0 && (
                  <div className="bg-white/5 rounded-lg p-4">
                    <p className="text-sm mb-2">Selected features:</p>
                    <div className="flex flex-wrap gap-2">
                      {formData.features.map((feature) => (
                        <span
                          key={feature}
                          className="bg-purple-500 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                        >
                          {feature}
                          <button
                            type="button"
                            onClick={() => handleFeatureRemove(feature)}
                            className="hover:text-red-300"
                          >
                            ✕
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex gap-4 mt-8">
            <button
              type="button"
              onClick={() => setStep(Math.max(1, step - 1))}
              disabled={step === 1}
              className="flex-1 px-6 py-3 border border-white/30 rounded-xl hover:bg-white/10 transition-all disabled:opacity-50"
            >
              Back
            </button>
            <button
              type="button"
              onClick={(e) => {
                if (step < 3) {
                  setStep(step + 1);
                } else {
                  handleSubmit(e);
                }
              }}
              disabled={uploading}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50"
            >
              {uploading ? 'Creating...' : step < 3 ? 'Next' : 'Create Listing'}
            </button>
          </div>
        </motion.form>
      </div>
    </div>
  );
};

export default CreateListing;
