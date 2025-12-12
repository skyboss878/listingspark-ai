import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import api from '../api';
import toast from 'react-hot-toast';

const ViewListing = () => {
  const { listingId } = useParams();
  const navigate = useNavigate();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchListing();
  }, [listingId]);

  const fetchListing = async () => {
    try {
      const response = await api.get(`/listings/${listingId}`);
      setListing(response.data);
    } catch (error) {
      toast.error('Failed to load listing');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-16 h-16 border-4 border-purple-400 border-t-transparent rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-xl">Loading listing...</p>
        </div>
      </div>
    );
  }

  if (!listing) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-white hover:text-purple-300 transition-colors"
          >
            ← Back to Dashboard
          </button>
          <div className="flex gap-2">
            <button
              onClick={() => navigate(`/edit-listing/${listing.id}`)}
              className="bg-indigo-600 px-6 py-2 rounded-lg hover:bg-indigo-700 transition-all"
            >
              ✏️ Edit Listing
            </button>
          </div>
        </div>

        {/* Listing Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20"
        >
          {/* Main Info */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">{listing.address}</h1>
            <p className="text-2xl text-purple-200 mb-4">{listing.city}, {listing.state} {listing.zip_code}</p>
            <p className="text-5xl font-bold text-green-400">${listing.price?.toLocaleString()}</p>
          </div>

          {/* Property Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            {listing.bedrooms && (
              <div className="bg-purple-600/20 rounded-lg p-4">
                <p className="text-purple-300 text-sm mb-1">Bedrooms</p>
                <p className="text-3xl font-bold">{listing.bedrooms}</p>
              </div>
            )}
            {listing.bathrooms && (
              <div className="bg-purple-600/20 rounded-lg p-4">
                <p className="text-purple-300 text-sm mb-1">Bathrooms</p>
                <p className="text-3xl font-bold">{listing.bathrooms}</p>
              </div>
            )}
            <div className="bg-purple-600/20 rounded-lg p-4">
              <p className="text-purple-300 text-sm mb-1">Square Feet</p>
              <p className="text-3xl font-bold">{listing.square_feet?.toLocaleString()}</p>
            </div>
            {listing.lot_size && (
              <div className="bg-purple-600/20 rounded-lg p-4">
                <p className="text-purple-300 text-sm mb-1">Lot Size</p>
                <p className="text-3xl font-bold">{listing.lot_size} acres</p>
              </div>
            )}
          </div>

          {/* Commercial Fields */}
          {listing.property_type === 'commercial' && (
            <div className="grid grid-cols-3 gap-6 mb-8">
              {listing.office_spaces && (
                <div className="bg-blue-600/20 rounded-lg p-4">
                  <p className="text-blue-300 text-sm mb-1">Office Spaces</p>
                  <p className="text-2xl font-bold">{listing.office_spaces}</p>
                </div>
              )}
              {listing.parking_spaces && (
                <div className="bg-blue-600/20 rounded-lg p-4">
                  <p className="text-blue-300 text-sm mb-1">Parking Spaces</p>
                  <p className="text-2xl font-bold">{listing.parking_spaces}</p>
                </div>
              )}
              {listing.loading_docks && (
                <div className="bg-blue-600/20 rounded-lg p-4">
                  <p className="text-blue-300 text-sm mb-1">Loading Docks</p>
                  <p className="text-2xl font-bold">{listing.loading_docks}</p>
                </div>
              )}
            </div>
          )}

          {/* Land Fields */}
          {listing.property_type === 'land' && (
            <div className="grid grid-cols-3 gap-6 mb-8">
              {listing.zoning && (
                <div className="bg-green-600/20 rounded-lg p-4">
                  <p className="text-green-300 text-sm mb-1">Zoning</p>
                  <p className="text-xl font-bold">{listing.zoning}</p>
                </div>
              )}
              {listing.topography && (
                <div className="bg-green-600/20 rounded-lg p-4">
                  <p className="text-green-300 text-sm mb-1">Topography</p>
                  <p className="text-xl font-bold">{listing.topography}</p>
                </div>
              )}
              {listing.utilities && (
                <div className="bg-green-600/20 rounded-lg p-4">
                  <p className="text-green-300 text-sm mb-1">Utilities</p>
                  <p className="text-xl font-bold">{listing.utilities}</p>
                </div>
              )}
            </div>
          )}

          {/* Custom Fields */}
          {listing.custom_fields && Object.keys(listing.custom_fields).length > 0 && (
            <div className="mb-8">
              <h3 className="text-2xl font-bold mb-4">Additional Details</h3>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(listing.custom_fields).map(([key, value]) => (
                  <div key={key} className="bg-white/5 rounded-lg p-4">
                    <p className="text-purple-300 text-sm mb-1">{key}</p>
                    <p className="text-xl font-semibold">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Description */}
          {listing.description && (
            <div className="mb-8">
              <h3 className="text-2xl font-bold mb-4">Description</h3>
              <p className="text-lg text-purple-100 leading-relaxed">{listing.description}</p>
            </div>
          )}

          {/* AI Generated Content */}
          {listing.ai_content && (
            <div className="mb-8">
              <h3 className="text-2xl font-bold mb-4">🤖 AI Generated Content</h3>
              <div className="space-y-4">
                {listing.ai_content.headline && (
                  <div className="bg-purple-600/20 rounded-lg p-4">
                    <p className="text-purple-300 text-sm mb-2">Headline</p>
                    <p className="text-xl font-bold">{listing.ai_content.headline}</p>
                  </div>
                )}
                {listing.ai_content.description && (
                  <div className="bg-purple-600/20 rounded-lg p-4">
                    <p className="text-purple-300 text-sm mb-2">AI Description</p>
                    <p className="text-lg">{listing.ai_content.description}</p>
                  </div>
                )}
                {listing.ai_content.social_captions && (
                  <div className="bg-purple-600/20 rounded-lg p-4">
                    <p className="text-purple-300 text-sm mb-2">Social Media Captions</p>
                    <div className="space-y-2">
                      {Object.entries(listing.ai_content.social_captions).map(([platform, caption]) => (
                        <div key={platform} className="bg-white/5 rounded p-3">
                          <p className="text-xs text-purple-200 uppercase mb-1">{platform}</p>
                          <p className="text-sm">{caption}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Features */}
          {listing.features && listing.features.length > 0 && (
            <div className="mb-8">
              <h3 className="text-2xl font-bold mb-4">Features</h3>
              <div className="flex flex-wrap gap-2">
                {listing.features.map((feature, index) => (
                  <span
                    key={index}
                    className="bg-purple-600 px-4 py-2 rounded-full text-sm"
                  >
                    {feature}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Status */}
          <div className="flex items-center justify-between pt-6 border-t border-white/20">
            <div>
              <p className="text-purple-300 text-sm mb-1">Status</p>
              <p className="text-2xl font-bold capitalize">{listing.status?.replace('_', ' ')}</p>
            </div>
            <div className="text-right">
              <p className="text-purple-300 text-sm mb-1">Property Type</p>
              <p className="text-2xl font-bold capitalize">{listing.property_type?.replace('_', ' ')}</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default ViewListing;
