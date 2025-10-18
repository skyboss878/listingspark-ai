import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const Camera360Capture = ({ onCapture, onClose }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const [capturedFrames, setCapturedFrames] = useState([]);
  const [progress, setProgress] = useState(0);
  const [deviceOrientation, setDeviceOrientation] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);

  const TOTAL_FRAMES = 36; // 36 frames for 360° (10° per frame)
  

  const handleOrientation = (event) => {
    setDeviceOrientation({
      alpha: event.alpha,
      beta: event.beta,
      gamma: event.gamma
    });
  };

  useEffect(() => {
    startCamera();

    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
      DeviceOrientationEvent.requestPermission()
        .then(permission => {
          if (permission === 'granted') {
            window.addEventListener('deviceorientation', handleOrientation);
          }
        })
        .catch(console.error);
    } else {
      window.addEventListener('deviceorientation', handleOrientation);
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      window.removeEventListener('deviceorientation', handleOrientation);
    };
  }, [stream]);

  const startCamera = async () => {
    try {
      // Request camera with highest resolution
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 4096 },
          height: { ideal: 2048 }
        },
        audio: false
      });

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setCameraActive(true);
        toast.success('Camera activated!');
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      toast.error('Could not access camera. Please grant permissions.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setCameraActive(false);
    }
  };

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    // Set canvas to video dimensions
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Return as blob
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob);
      }, 'image/jpeg', 0.95);
    });
  };

  const startPanoramicCapture = async () => {
    if (capturedFrames.length > 0) {
      setCapturedFrames([]);
    }

    setCapturing(true);
    toast.success('Rotate slowly 360° while keeping device steady');

    const frames = [];
    const interval = setInterval(async () => {
      const frame = await captureFrame();
      if (frame) {
        frames.push(frame);
        setCapturedFrames([...frames]);
        setProgress((frames.length / TOTAL_FRAMES) * 100);

        if (frames.length >= TOTAL_FRAMES) {
          clearInterval(interval);
          setCapturing(false);
          toast.success('Capture complete! Processing panorama...');
          await stitchPanorama(frames);
        }
      }
    }, 500); // Capture every 500ms

    // Auto-stop after 30 seconds
    setTimeout(() => {
      if (capturing) {
        clearInterval(interval);
        setCapturing(false);
        if (frames.length >= 12) { // Minimum 12 frames (120°)
          toast.success('Processing partial panorama...');
          stitchPanorama(frames);
        } else {
          toast.error('Not enough frames captured. Try again.');
        }
      }
    }, 30000);
  };

  const stitchPanorama = async (frames) => {
    try {
      // Create panorama canvas
      const panoCanvas = document.createElement('canvas');
      const panoContext = panoCanvas.getContext('2d');

      // Calculate panorama dimensions (2:1 aspect ratio)
      const frameWidth = videoRef.current.videoWidth;
      // const frameHeight = videoRef.current.videoHeight;
      const panoWidth = Math.max(frameWidth * 2, 4096);
      const panoHeight = panoWidth / 2;

      panoCanvas.width = panoWidth;
      panoCanvas.height = panoHeight;

      // Stitch frames horizontally
      const frameWidthInPano = panoWidth / frames.length;

      for (let i = 0; i < frames.length; i++) {
        const img = await createImageBitmap(frames[i]);
        const x = i * frameWidthInPano;
        panoContext.drawImage(img, x, 0, frameWidthInPano, panoHeight);
      }

      // Convert to blob
      panoCanvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], '360-panorama.jpg', { type: 'image/jpeg' });
          onCapture(file);
          stopCamera();
        }
      }, 'image/jpeg', 0.9);

    } catch (error) {
      console.error('Error stitching panorama:', error);
      toast.error('Failed to create panorama');
    }
  };

  const takeSingleShot = async () => {
    const frame = await captureFrame();
    if (frame) {
      const file = new File([frame], 'capture.jpg', { type: 'image/jpeg' });
      onCapture(file);
      stopCamera();
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/80 to-transparent p-4">
        <div className="flex justify-between items-center">
          <h2 className="text-white text-xl font-bold">
            📸 360° Camera
          </h2>
          <button
            onClick={() => {
              stopCamera();
              onClose();
            }}
            className="text-white text-2xl hover:text-red-400"
          >
            ×
          </button>
        </div>
      </div>

      {/* Video Feed */}
      <div className="flex-1 relative">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* Capture Overlay */}
        {capturing && (
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="text-center"
            >
              <div className="text-white text-6xl mb-4">🔄</div>
              <div className="text-white text-xl font-semibold mb-2">
                Keep rotating slowly...
              </div>
              <div className="w-64 bg-white/20 rounded-full h-4 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                />
              </div>
              <div className="text-white mt-2">
                {capturedFrames.length} / {TOTAL_FRAMES} frames
              </div>
            </motion.div>
          </div>
        )}

        {/* Orientation Guide */}
        {deviceOrientation && !capturing && (
          <div className="absolute top-20 left-4 bg-black/60 text-white p-3 rounded-lg text-sm">
            <div>Direction: {Math.round(deviceOrientation.alpha)}°</div>
            <div>Tilt: {Math.round(deviceOrientation.beta)}°</div>
          </div>
        )}

        {/* Grid Overlay */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="w-full h-full grid grid-cols-3 grid-rows-3">
            {[...Array(9)].map((_, i) => (
              <div key={i} className="border border-white/20" />
            ))}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6">
        <div className="max-w-2xl mx-auto">
          {/* Instructions */}
          <div className="text-center text-white mb-4 text-sm">
            <p className="mb-2">
              <strong>For best results:</strong>
            </p>
            <ul className="text-left inline-block text-xs space-y-1">
              <li>• Hold device vertically and rotate slowly</li>
              <li>• Keep camera level with horizon</li>
              <li>• Make sure room is well-lit</li>
              <li>• Complete full 360° rotation</li>
            </ul>
          </div>

          {/* Capture Buttons */}
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={startPanoramicCapture}
              disabled={capturing || !cameraActive}
              className="btn-viral py-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {capturing ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Capturing...
                </span>
              ) : (
                <>🔄 360° Panorama</>
              )}
            </button>

            <button
              onClick={takeSingleShot}
              disabled={capturing || !cameraActive}
              className="px-6 py-4 border-2 border-white/50 rounded-xl text-white font-semibold hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              📷 Single Shot
            </button>
          </div>

          {/* Preview Thumbnails */}
          {capturedFrames.length > 0 && (
            <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
              {capturedFrames.slice(-10).map((_, i) => (
                <div
                  key={i}
                  className="w-16 h-16 bg-white/20 rounded flex-shrink-0 flex items-center justify-center text-white text-xs"
                >
                  Frame {capturedFrames.length - 9 + i}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Camera360Capture;
