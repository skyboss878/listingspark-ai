import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api' || 'http://localhost:8000/api';

const VirtualTourUpload = ({ propertyId, onTourCreated }) => {
  const [uploading, setUploading] = useState(false);
  const [sceneName, setSceneName] = useState('Main Room');

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Check file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    // Check aspect ratio for 360 images
    const img = new Image();
    img.onload = async () => {
      const aspectRatio = img.width / img.height;
      if (aspectRatio < 1.8 || aspectRatio > 2.2) {
        toast.error('Please upload a 360° image (2:1 aspect ratio). Standard photos won\'t work for virtual tours.');
        return;
      }

      await uploadTour(file);
    };
    img.src = URL.createObjectURL(file);
  };

  const uploadTour = async (file) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('scene_name', sceneName);

    try {
      const response = await axios.post(`${API}/properties/${propertyId}/upload-360`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          toast.loading(`Uploading... ${percentCompleted}%`, { id: 'upload' });
        },
      });

      toast.success('360° tour uploaded! Processing...', { id: 'upload' });
      
      // Poll for completion
      pollTourStatus(response.data.tour_id);
      
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Upload failed', { id: 'upload' });
    } finally {
      setUploading(false);
    }
  };

  const pollTourStatus = async (tourId) => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API}/properties/${propertyId}/tours`);
        const tour = response.data.find(t => t.id === tourId);
        
        if (tour) {
          if (tour.processing_status === 'completed') {
            toast.success('Virtual tour ready!');
            onTourCreated && onTourCreated(tour);
            return;
          } else if (tour.processing_status === 'failed') {
            toast.error('Tour processing failed');
            return;
          }
        }
        
        // Continue polling
        setTimeout(checkStatus, 2000);
      } catch (error) {
        console.error('Status check error:', error);
      }
    };
    
    checkStatus();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png']
    },
    maxFiles: 1
  });

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-2">Scene Name</label>
        <input
          type="text"
          value={sceneName}
          onChange={(e) => setSceneName(e.target.value)}
          className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 focus:border-purple-400 focus:outline-none"
          placeholder="e.g., Living Room, Kitchen, Master Bedroom"
        />
      </div>

      <motion.div
        {...getRootProps()}
        whileHover={{ scale: 1.02 }}
        className={`glass rounded-xl p-8 text-center cursor-pointer transition-all ${
          isDragActive ? 'border-purple-400 bg-purple-500/20' : 'border-white/20'
        } ${uploading ? 'pointer-events-none opacity-50' : ''}`}
      >
        <input {...getInputProps()} />
        
        <div className="text-6xl mb-4">360°</div>
        
        {uploading ? (
          <div>
            <div className="spinner mx-auto mb-4"></div>
            <p>Processing your 360° image...</p>
          </div>
        ) : isDragActive ? (
          <div>
            <h3 className="text-xl font-semibold mb-2">Drop your 360° image here</h3>
            <p className="opacity-80">Release to upload</p>
          </div>
        ) : (
          <div>
            <h3 className="text-xl font-semibold mb-2">Upload 360° Image</h3>
            <p className="opacity-80 mb-4">
              Drag and drop your 360° equirectangular image, or click to browse
            </p>
            <div className="text-sm opacity-60">
              <p>📐 Required: 2:1 aspect ratio (e.g., 4096x2048)</p>
              <p>📱 Taken with: 360° camera, smartphone 360 mode, or panorama</p>
              <p>📄 Formats: JPG, PNG (max 50MB)</p>
            </div>
          </div>
        )}
      </motion.div>

      <div className="glass rounded-lg p-4">
        <h4 className="font-semibold mb-2">How to get 360° images:</h4>
        <ul className="text-sm opacity-80 space-y-1">
          <li>• Use a 360° camera (Ricoh Theta, Insta360, etc.)</li>
          <li>• iPhone/Android panorama mode (full 360°)</li>
          <li>• Google Street View app 360° mode</li>
          <li>• Professional 360° photography services</li>
        </ul>
      </div>
    </div>
  );
};

export default VirtualTourUpload;
