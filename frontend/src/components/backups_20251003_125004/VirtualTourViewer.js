import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api' || 'http://localhost:8000/api';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const VirtualTourViewer = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [tours, setTours] = useState([]);
  const [selectedTour, setSelectedTour] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTours();
  }, [propertyId]);

  const fetchTours = async () => {
    try {
      const response = await axios.get(`${API}/properties/${propertyId}/tours`);
      const completedTours = response.data.filter(tour => tour.processing_status === 'completed');
      setTours(completedTours);
      if (completedTours.length > 0) {
        setSelectedTour(completedTours[0]);
        // Track tour view
        trackTourView(completedTours[0].id);
      }
    } catch (error) {
      console.error('Error fetching tours:', error);
    } finally {
      setLoading(false);
    }
  };

  const trackTourView = async (tourId) => {
    try {
      await axios.post(`${API}/tours/${tourId}/view`);
    } catch (error) {
      console.error('Error tracking tour view:', error);
    }
  };

  const selectTour = (tour) => {
    setSelectedTour(tour);
    trackTourView(tour.id);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="spinner mb-4"></div>
          <p>Loading virtual tours...</p>
        </div>
      </div>
    );
  }

  if (tours.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="text-6xl mb-4">🔄</div>
          <h2 className="text-2xl font-bold mb-2">No Virtual Tours Available</h2>
          <p className="opacity-80 mb-6">Upload 360° images to create virtual tours</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => navigate(`/upload-tour/${propertyId}`)}
              className="btn-viral"
            >
              Add Virtual Tour
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="border border-white/30 rounded-lg px-4 py-2 hover:bg-white/10 transition-all"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-sm border-b border-white/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-white text-2xl hover:text-purple-300 transition-colors"
              >
                ←
              </button>
              <div>
                <h1 className="text-white text-xl font-bold">360° Virtual Tour</h1>
                <p className="text-purple-200 text-sm">Interactive Property Experience</p>
              </div>
            </div>
            
            {tours.length > 1 && (
              <div className="flex gap-2">
                {tours.map((tour, index) => (
                  <button
                    key={tour.id}
                    onClick={() => selectTour(tour)}
                    className={`px-4 py-2 rounded-lg text-sm transition-all ${
                      selectedTour?.id === tour.id 
                        ? 'bg-purple-500 text-white' 
                        : 'bg-white/20 text-white hover:bg-white/30'
                    }`}
                  >
                    {tour.tour_name}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tour Viewer */}
      {selectedTour && (
        <div className="h-screen">
          <iframe
            src={`${BACKEND_URL}${selectedTour.tour_url}`}
            className="w-full h-full border-0"
            allowFullScreen
            title="360° Virtual Tour"
          />
        </div>
      )}

      {/* Tour Controls */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-10">
        <div className="glass rounded-full px-6 py-3 flex items-center gap-4">
          <span className="text-white text-sm">🔄 360° Tour Active</span>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-purple-300 hover:text-white transition-colors text-sm"
          >
            Exit Tour
          </button>
        </div>
      </div>
    </div>
  );
};

export default VirtualTourViewer;
