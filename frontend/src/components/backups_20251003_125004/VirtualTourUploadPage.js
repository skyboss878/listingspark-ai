import React, { useState, useEffect, useContext } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { UserContext } from '../App';
import VirtualTourUpload from './VirtualTourUpload';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api' || 'http://localhost:8000/api';

const VirtualTourUploadPage = () => {
  const { propertyId } = useParams();
  const { user } = useContext(UserContext);
  const navigate = useNavigate();
  const [property, setProperty] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProperty();
  }, [propertyId]);

  const fetchProperty = async () => {
    try {
      const response = await axios.get(`${API}/properties/${user.id}`);
      const foundProperty = response.data.find(p => p.id === propertyId);
      setProperty(foundProperty);
    } catch (error) {
      console.error('Error fetching property:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTourCreated = (tour) => {
    navigate(`/virtual-tour/${propertyId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="spinner mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <p>Property not found</p>
          <button onClick={() => navigate('/dashboard')} className="btn-viral mt-4">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-2xl hover:text-purple-300 transition-colors"
          >
            ←
          </button>
          <div className="flex-1">
            <motion.h1 
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              className="text-3xl font-bold mb-2"
            >
              Add 360° Virtual Tour
            </motion.h1>
            <p className="text-purple-200">{property.title}</p>
            <p className="text-purple-300 text-sm">{property.address}</p>
          </div>
        </div>

        {/* Upload Interface */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="max-w-4xl mx-auto"
        >
          <div className="glass rounded-2xl p-8">
            <VirtualTourUpload 
              propertyId={propertyId}
              onTourCreated={handleTourCreated}
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default VirtualTourUploadPage;
