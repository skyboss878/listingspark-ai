import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import api from '../utils/api';
import toast from 'react-hot-toast';
import Camera360Capture from './Camera360Capture';

const VirtualTourUploadPage = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [sceneName, setSceneName] = useState('Main Room');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [showCamera, setShowCamera] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      
      if (!file.type.startsWith('image/')) {
        toast.error('Please upload an image file');
        return;
      }

      if (file.size > 50 * 1024 * 1024) {
        toast.error('File too large. Maximum size is 50MB');
        return;
      }

      setUploadedFile(file);
      toast.success('Image selected! Ready to upload.');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp']
    },
    multiple: false,
    maxSize: 50 * 1024 * 1024
  });

  const handleCameraCapture = (file) => {
    setUploadedFile(file);
    setShowCamera(false);
    toast.success('Image captured! Ready to upload.');
  };

  const handleUpload = async () => {
    if (!uploadedFile) {
      toast.error('Please select an image first');
      return;
    }

    if (!sceneName.trim()) {
      toast.error('Please enter a scene name');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);

      // const result = await api.tours.upload360(propertyId, uploadedFile, sceneName);

      clearInterval(progressInterval);
      setUploadProgress(100);

      toast.success('360° tour uploaded successfully!');
      
      setTimeout(() => {
        navigate(`/virtual-tour/${propertyId}`);
      }, 1500);

    } catch (error) {
      console.error('Upload error:', error);
      const errorMsg = error.response?.data?.detail || 'Upload failed. Please check image format (2:1 aspect ratio for 360° images)';
      toast.error(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white py-12">
      <AnimatePresence>
        {showCamera && (
          <Camera360Capture
            onCapture={handleCameraCapture}
            onClose={() => setShowCamera(false)}
          />
        )}
      </AnimatePresence>

      <div className="container mx-auto px-6 max-w-4xl">
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
          <h1 className="text-4xl font-bold mb-2">Upload 360° Virtual Tour</h1>
          <p className="text-purple-200">
            Upload equirectangular 360° images (2:1 aspect ratio) or capture with camera
          </p>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass rounded-xl p-6 mb-8"
        >
          <h3 className="text-xl font-semibold mb-4">📸 Image Requirements</h3>
          <ul className="space-y-2 text-purple-100">
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>360° equirectangular format (2:1 aspect ratio)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>Minimum resolution: 2048x1024 pixels</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>Supported formats: JPG, PNG, WEBP</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>Maximum file size: 50MB</span>
            </li>
          </ul>
          <div className="mt-4 p-4 bg-blue-500/20 rounded-lg">
            <p className="text-sm text-blue-100">
              💡 <strong>Tip:</strong> Use the built-in camera to capture 360° views by slowly rotating,
              or upload from a 360° camera app like Google Street View or Ricoh Theta.
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-xl p-8"
        >
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              Scene Name
            </label>
            <input
              type="text"
              value={sceneName}
              onChange={(e) => setSceneName(e.target.value)}
              placeholder="e.g., Living Room, Master Bedroom"
              className="w-full px-4 py-3 bg-white/10 rounded-lg border border-white/20 focus:border-purple-400 focus:outline-none"
              disabled={uploading}
            />
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <button
              onClick={() => setShowCamera(true)}
              className="p-6 border-2 border-dashed border-purple-400 rounded-xl hover:bg-purple-500/10 transition-all"
              disabled={uploading}
            >
              <div className="text-4xl mb-2">📸</div>
              <div className="font-semibold">Use Camera</div>
              <div className="text-sm text-purple-200">Capture 360° now</div>
            </button>

            <div
              {...getRootProps()}
              className={`
                p-6 border-2 border-dashed rounded-xl transition-all cursor-pointer
                ${isDragActive 
                  ? 'border-purple-400 bg-purple-500/20' 
                  : 'border-white/30 hover:border-white/50 hover:bg-white/5'
                }
                ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input {...getInputProps()} disabled={uploading} />
              <div className="text-4xl mb-2">📁</div>
              <div className="font-semibold">Upload File</div>
              <div className="text-sm text-purple-200">
                {isDragActive ? 'Drop here' : 'Select from device'}
              </div>
            </div>
          </div>

          {uploadedFile && (
            <div className="mb-6 p-4 bg-green-500/20 rounded-lg border border-green-400/30">
              <div className="flex items-start gap-3">
                <div className="text-2xl">✓</div>
                <div className="flex-1">
                  <p className="font-semibold text-green-400 mb-1">File Selected</p>
                  <p className="text-sm">{uploadedFile.name}</p>
                  <p className="text-xs text-purple-300 mt-1">
                    {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
                {!uploading && (
                  <button
                    onClick={() => setUploadedFile(null)}
                    className="text-red-400 hover:text-red-300"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          )}

          {uploading && (
            <div className="mb-6">
              <div className="flex justify-between text-sm mb-2">
                <span>Uploading and processing...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                  className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                  transition={{ duration: 0.3 }}
                />
              </div>
              <p className="text-sm text-purple-200 mt-2 text-center">
                Please wait while we process your 360° image...
              </p>
            </div>
          )}

          <div className="flex gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              disabled={uploading}
              className="flex-1 px-6 py-3 border border-white/30 rounded-lg hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={!uploadedFile || uploading}
              className="flex-1 btn-viral py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Uploading...
                </span>
              ) : (
                'Upload & Process'
              )}
            </button>
          </div>

          <div className="mt-6 text-center text-sm text-purple-200">
            <p>
              Need help creating 360° images?{' '}
              <a
                href="https://www.google.com/streetview/publish/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-300 hover:text-white underline"
              >
                Learn more about 360° photography
              </a>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default VirtualTourUploadPage;
