import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import api from '../api';
import { getErrorMessage } from '../utils/errorHelpers';

const OpenHouse = () => {
  const { listingId } = useParams();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [imgIndex, setImgIndex] = useState(0);

  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '' });

  useEffect(() => {
    const fetchListing = async () => {
      try {
        const response = await api.get(`/listings/${listingId}/open-house`);
        setListing(response.data);
      } catch (error) {
        setLoadError(getErrorMessage(error, 'This listing could not be found.'));
      } finally {
        setLoading(false);
      }
    };
    fetchListing();
  }, [listingId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post(`/listings/${listingId}/open-house/lead`, form);
      setSubmitted(true);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Something went wrong. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p>Loading property...</p>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white p-6">
        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20 max-w-md text-center">
          <div className="text-5xl mb-4">🏠</div>
          <h2 className="text-2xl font-bold mb-2">Listing Not Found</h2>
          <p className="text-purple-200">{loadError}</p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20 max-w-md text-center"
        >
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold mb-2">Thanks, {form.first_name}!</h2>
          <p className="text-purple-200">
            The agent will reach out with more details about {listing?.address}. Enjoy the rest of the open house!
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      {listing?.images?.length > 0 && (
        <div className="relative h-64 sm:h-80 bg-black/30 overflow-hidden">
          <img
            src={listing.images[imgIndex]}
            alt={listing.address}
            className="w-full h-full object-cover"
          />
          {listing.images.length > 1 && (
            <div className="absolute bottom-3 left-0 right-0 flex justify-center gap-1.5">
              {listing.images.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setImgIndex(i)}
                  className={`w-2 h-2 rounded-full ${i === imgIndex ? 'bg-white' : 'bg-white/40'}`}
                />
              ))}
            </div>
          )}
        </div>
      )}

      <div className="max-w-lg mx-auto p-4 sm:p-6">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold">{listing?.address}</h1>
          <p className="text-purple-200">{listing?.city}, {listing?.state} {listing?.zip_code}</p>
          <p className="text-3xl font-bold mt-2 text-green-400">
            ${listing?.price?.toLocaleString()}
          </p>
        </div>

        <div className="flex justify-center gap-6 mb-6 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
          <div className="text-center">
            <div className="text-xl font-bold">{listing?.bedrooms ?? '—'}</div>
            <div className="text-xs text-purple-300">Beds</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold">{listing?.bathrooms ?? '—'}</div>
            <div className="text-xs text-purple-300">Baths</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold">{listing?.square_feet?.toLocaleString() ?? '—'}</div>
            <div className="text-xs text-purple-300">Sq Ft</div>
          </div>
        </div>

        {listing?.description && (
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 mb-6">
            <p className="text-sm text-purple-50 leading-relaxed">{listing.description}</p>
          </div>
        )}

        {listing?.features?.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {listing.features.map((f, i) => (
              <span key={i} className="text-xs bg-purple-600/40 px-3 py-1 rounded-full">
                {f}
              </span>
            ))}
          </div>
        )}

        <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/20">
          <h3 className="font-bold text-lg mb-1">Want more information?</h3>
          <p className="text-sm text-purple-300 mb-4">Leave your details and the agent will follow up.</p>

          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <input required name="first_name" value={form.first_name} onChange={handleChange}
                placeholder="First name" className="px-3 py-2.5 rounded-lg bg-white/10 border border-white/20 placeholder-white/50" />
              <input required name="last_name" value={form.last_name} onChange={handleChange}
                placeholder="Last name" className="px-3 py-2.5 rounded-lg bg-white/10 border border-white/20 placeholder-white/50" />
            </div>
            <input required type="email" name="email" value={form.email} onChange={handleChange}
              placeholder="Email" className="w-full px-3 py-2.5 rounded-lg bg-white/10 border border-white/20 placeholder-white/50 mb-3" />
            <input type="tel" name="phone" value={form.phone} onChange={handleChange}
              placeholder="Phone (optional)" className="w-full px-3 py-2.5 rounded-lg bg-white/10 border border-white/20 placeholder-white/50 mb-4" />
            <button type="submit" disabled={submitting}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 py-3 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50">
              {submitting ? 'Submitting...' : "I'm Interested"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default OpenHouse;
