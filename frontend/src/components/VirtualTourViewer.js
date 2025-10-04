// src/components/VirtualTourViewer.js
import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import api, { BACKEND_URL } from '../utils/api';
import toast from 'react-hot-toast';

const VirtualTourViewer = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [tours, setTours] = useState([]);
  const [selectedTour, setSelectedTour] = useState(null);


  const loadTours = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.tours.getPropertyTours(propertyId);
      setTours(data);

      if (data.length > 0) {
        const completedTour = data.find(t => t.processing_status === 'completed');
        if (completedTour) {
          setSelectedTour(completedTour);
          await api.tours.trackView(completedTour.id);
        }
      }
    } catch (error) {
      console.error('Error loading tours:'  error);
      toast.error('Failed to load virtual tours');
    } finally {
      setLoading(false);
    }
  }, [propertyId]);

  useEffect(() => {
    loadTours();
  }, [loadTours]);

  const loadTours = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.tours.getPropertyTours(propertyId);
      setTours(data);
      
      if (data.length > 0) {
        // Select the first completed tour
        const completedTour = data.find(t => t.processing_status === 'completed');
        if (completedTour) {
          setSelectedTour(completedTour);
          await api.tours.trackView(completedTour.id);
        }
      }
    } catch (error) {
      console.error('Error loading tours:', error);
      toast.error('Failed to load virtual tours');
    } finally {
      setLoading(false);
    }
  }, [propertyId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p>Loading virtual tour...</p>
        </div>
      </div>
    );
  }

  if (tours.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white py-12">
        <div className="container mx-auto px-6 max-w-4xl">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-purple-200 hover:text-white mb-8 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          
          <div className="glass rounded-xl p-12 text-center">
            <div className="text-6xl mb-4">🔄</div>
            <h3 className="text-2xl font-semibold mb-4">No Virtual Tours Yet</h3>
            <p className="text-purple-200 mb-6">
              Upload a 360° image to create an immersive virtual tour
            </p>
            <button
              onClick={() => navigate(`/upload-tour/${propertyId}`)}
              className="btn-viral px-8 py-4"
            >
              Upload 360° Tour
            </button>
          </div>
        </div>
      </div>
    );
  }

  const completedTours = tours.filter(t => t.processing_status === 'completed');
  const processingTours = tours.filter(t => t.processing_status === 'processing');
  const failedTours = tours.filter(t => t.processing_status === 'failed');

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      {/* Header */}
      <div className="container mx-auto px-6 py-8">
        <button
          onClick={() => navigate('/dashboard')}
          className="text-purple-200 hover:text-white mb-4 flex items-center gap-2"
        >
          ← Back to Dashboard
        </button>
        <h1 className="text-3xl font-bold mb-2">Virtual Tours</h1>
        <p className="text-purple-200">Explore your property in 360°</p>
      </div>

      {/* Tour Viewer */}
      {selectedTour && selectedTour.processing_status === 'completed' && (
        <div className="w-full" style={{ height: 'calc(100vh - 200px)' }}>
          <iframe
            src={api.tours.getTourUrl(selectedTour.id)}
            className="w-full h-full border-0"
            title="Virtual Tour"
            allow="accelerometer; gyroscope; fullscreen"
          />
        </div>
      )}

      {/* Tour List & Status */}
      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Completed Tours */}
          {completedTours.map((tour) => (
            <motion.div
              key={tour.id}
              whileHover={{ y: -5 }}
              onClick={() => setSelectedTour(tour)}
              className={`
                glass rounded-xl p-6 cursor-pointer transition-all
                ${selectedTour?.id === tour.id ? 'ring-2 ring-purple-400' : ''}
              `}
            >
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">🔄</span>
                <div>
                  <h3 className="font-semibold">{tour.tour_name}</h3>
                  <p className="text-sm text-green-400">Ready to view</p>
                </div>
              </div>
              {tour.thumbnail_url && (
                <img
                  src={`${BACKEND_URL}${tour.thumbnail_url}`}
                  alt={tour.tour_name}
                  className="w-full h-32 object-cover rounded-lg"
                />
              )}
              <div className="mt-4 text-sm text-purple-200">
                {tour.scene_count} scene{tour.scene_count !== 1 ? 's' : ''}
              </div>
            </motion.div>
          ))}

          {/* Processing Tours */}
          {processingTours.map((tour) => (
            <div key={tour.id} className="glass rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 border-4 border-purple-400 border-t-transparent rounded-full animate-spin" />
                <div>
                  <h3 className="font-semibold">{tour.tour_name}</h3>
                  <p className="text-sm text-yellow-400">Processing...</p>
                </div>
              </div>
              <p className="text-sm text-purple-200">
                Your tour is being processed. This may take a few minutes.
              </p>
            </div>
          ))}

          {/* Failed Tours */}
          {failedTours.map((tour) => (
            <div key={tour.id} className="glass rounded-xl p-6 border-2 border-red-500/30">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">⚠️</span>
                <div>
                  <h3 className="font-semibold">{tour.tour_name}</h3>
                  <p className="text-sm text-red-400">Processing failed</p>
                </div>
              </div>
              <p className="text-sm text-purple-200 mb-4">
                There was an error processing this tour. Please try uploading again.
              </p>
              <button
                onClick={() => navigate(`/upload-tour/${propertyId}`)}
                className="w-full px-4 py-2 border border-white/30 rounded-lg hover:bg-white/10 transition-all text-sm"
              >
                Upload New Tour
              </button>
            </div>
          ))}

          {/* Add New Tour */}
          <motion.div
            whileHover={{ y: -5 }}
            onClick={() => navigate(`/upload-tour/${propertyId}`)}
            className="glass rounded-xl p-6 cursor-pointer border-2 border-dashed border-white/30 hover:border-white/50 transition-all flex flex-col items-center justify-center text-center min-h-[200px]"
          >
            <div className="text-5xl mb-3">➕</div>
            <h3 className="font-semibold mb-2">Add New Scene</h3>
            <p className="text-sm text-purple-200">
              Upload another 360° image
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default VirtualTourViewer;
