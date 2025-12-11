import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

const ProCamera360 = ({ onCapture, onClose, propertyType = 'luxury' }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [mode, setMode] = useState('guided'); // 'guided', 'auto', 'manual'
  const [capturing, setCapturing] = useState(false);
  const [capturedFrames, setCapturedFrames] = useState([]);
  const [progress, setProgress] = useState(0);
  const [deviceOrientation, setDeviceOrientation] = useState(null);
  const [initialOrientation, setInitialOrientation] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [currentRoom, setCurrentRoom] = useState('');
  const [aiEnhancement, setAiEnhancement] = useState(true);
  const [autoStabilization, setAutoStabilization] = useState(true);
  const [showGrid, setShowGrid] = useState(true);
  const [captureQuality, setCaptureQuality] = useState('ultra'); // 'high', 'ultra', 'pro'
  
  const QUALITY_SETTINGS = {
    high: { frames: 24, width: 3840, height: 1920, quality: 0.85 },
    ultra: { frames: 36, width: 4096, height: 2048, quality: 0.92 },
    pro: { frames: 60, width: 8192, height: 4096, quality: 0.95 }
  };

  const settings = QUALITY_SETTINGS[captureQuality];

  // Enhanced orientation tracking
  const handleOrientation = useCallback((event) => {
    const newOrientation = {
      alpha: event.alpha || 0,
      beta: event.beta || 0,
      gamma: event.gamma || 0
    };
    
    setDeviceOrientation(newOrientation);
    
    // Calculate rotation from initial position
    if (initialOrientation && mode === 'guided') {
      const rotationDegrees = Math.abs(newOrientation.alpha - initialOrientation.alpha);
      const normalizedRotation = rotationDegrees > 180 ? 360 - rotationDegrees : rotationDegrees;
      setProgress((normalizedRotation / 360) * 100);
    }
  }, [initialOrientation, mode]);

  useEffect(() => {
    startCamera();

    // Request device orientation permission (iOS 13+)
    if (typeof DeviceOrientationEvent !== 'undefined' && 
        typeof DeviceOrientationEvent.requestPermission === 'function') {
      DeviceOrientationEvent.requestPermission()
        .then(permission => {
          if (permission === 'granted') {
            window.addEventListener('deviceorientation', handleOrientation);
          } else {
            toast.error('Orientation permission denied. Manual mode recommended.');
          }
        })
        .catch(err => {
          console.error('Orientation permission error:', err);
          toast('Using manual mode', { icon: '📱' });
        });
    } else {
      window.addEventListener('deviceorientation', handleOrientation);
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      window.removeEventListener('deviceorientation', handleOrientation);
    };
  }, [stream, handleOrientation]);

  const startCamera = async () => {
    try {
      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: settings.width },
          height: { ideal: settings.height },
          aspectRatio: { ideal: 2 },
          frameRate: { ideal: 30 }
        },
        audio: false
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setCameraActive(true);
        toast.success('Professional camera activated', { icon: '📸' });
      }
    } catch (error) {
      console.error('Camera error:', error);
      toast.error('Camera access required. Check permissions.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setCameraActive(false);
    }
  };

  // AI-Enhanced frame capture with auto-correction
  const captureEnhancedFrame = async () => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d', { alpha: false });

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Apply stabilization matrix if enabled
    if (autoStabilization && deviceOrientation) {
      ctx.save();
      // Calculate stabilization offset based on device tilt
      const tiltOffset = deviceOrientation.beta - 90; // Assume 90° is level
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate((-tiltOffset * Math.PI) / 180);
      ctx.translate(-canvas.width / 2, -canvas.height / 2);
    }

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    if (autoStabilization) {
      ctx.restore();
    }

    // AI Enhancement: Auto brightness, contrast, sharpness
    if (aiEnhancement) {
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      enhanceImageData(imageData);
      ctx.putImageData(imageData, 0, 0);
    }

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob);
      }, 'image/jpeg', settings.quality);
    });
  };

  // AI Image Enhancement Algorithm
  const enhanceImageData = (imageData) => {
    const data = imageData.data;
    let minBrightness = 255, maxBrightness = 0;
    
    // Calculate brightness range
    for (let i = 0; i < data.length; i += 4) {
      const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
      minBrightness = Math.min(minBrightness, brightness);
      maxBrightness = Math.max(maxBrightness, brightness);
    }
    
    const range = maxBrightness - minBrightness;
    const scale = range > 0 ? 255 / range : 1;
    
    // Apply auto-levels and contrast
    for (let i = 0; i < data.length; i += 4) {
      // Auto-levels
      data[i] = ((data[i] - minBrightness) * scale);
      data[i + 1] = ((data[i + 1] - minBrightness) * scale);
      data[i + 2] = ((data[i + 2] - minBrightness) * scale);
      
      // Boost contrast (S-curve)
      data[i] = applySCurve(data[i]);
      data[i + 1] = applySCurve(data[i + 1]);
      data[i + 2] = applySCurve(data[i + 2]);
      
      // Saturation boost for real estate
      const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
      const saturationBoost = 1.15;
      data[i] = clamp(avg + (data[i] - avg) * saturationBoost);
      data[i + 1] = clamp(avg + (data[i + 1] - avg) * saturationBoost);
      data[i + 2] = clamp(avg + (data[i + 2] - avg) * saturationBoost);
    }
  };

  const applySCurve = (value) => {
    const normalized = value / 255;
    const curved = normalized < 0.5 
      ? 2 * normalized * normalized 
      : 1 - 2 * (1 - normalized) * (1 - normalized);
    return clamp(curved * 255);
  };

  const clamp = (value) => Math.max(0, Math.min(255, value));

  // Guided 360° capture with voice prompts
  const startGuidedCapture = async () => {
    if (!initialOrientation && deviceOrientation) {
      setInitialOrientation(deviceOrientation);
    }

    setCapturedFrames([]);
    setCapturing(true);
    setProgress(0);

    // Voice prompt (if supported)
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(
        "Rotate slowly in a full circle. Keep the device level."
      );
      utterance.rate = 0.9;
      speechSynthesis.speak(utterance);
    }

    toast.success('Rotate 360° slowly and steadily', { duration: 5000 });

    const frames = [];
    let lastCaptureAngle = deviceOrientation?.alpha || 0;
    const angleIncrement = 360 / settings.frames;

    const captureInterval = setInterval(async () => {
      if (!deviceOrientation) return;

      const currentAngle = deviceOrientation.alpha;
      const angleDiff = Math.abs(currentAngle - lastCaptureAngle);

      // Capture when device has rotated enough
      if (angleDiff >= angleIncrement || frames.length === 0) {
        const frame = await captureEnhancedFrame();
        if (frame) {
          frames.push(frame);
          setCapturedFrames([...frames]);
          lastCaptureAngle = currentAngle;
          
          // Progress feedback
          const frameProgress = (frames.length / settings.frames) * 100;
          setProgress(frameProgress);

          if (frames.length >= settings.frames) {
            clearInterval(captureInterval);
            completeCaptureAndProcess(frames);
          }
        }
      }
    }, 200);

    // Safety timeout
    setTimeout(() => {
      clearInterval(captureInterval);
      if (frames.length >= settings.frames * 0.75) {
        completeCaptureAndProcess(frames);
      } else {
        setCapturing(false);
        toast.error('Not enough coverage. Try again.');
      }
    }, 60000);
  };

  // Auto capture mode - captures continuously
  const startAutoCapture = async () => {
    setCapturedFrames([]);
    setCapturing(true);
    toast.success('Auto-capturing. Rotate naturally.', { duration: 5000 });

    const frames = [];
    const startTime = Date.now();
    const captureDuration = 20000; // 20 seconds

    const captureLoop = setInterval(async () => {
      const frame = await captureEnhancedFrame();
      if (frame) {
        frames.push(frame);
        setCapturedFrames([...frames]);
        
        const elapsed = Date.now() - startTime;
        setProgress((elapsed / captureDuration) * 100);

        if (elapsed >= captureDuration) {
          clearInterval(captureLoop);
          completeCaptureAndProcess(frames);
        }
      }
    }, 500);
  };

  // Manual capture - user controls
  const captureManualFrame = async () => {
    const frame = await captureEnhancedFrame();
    if (frame) {
      const newFrames = [...capturedFrames, frame];
      setCapturedFrames(newFrames);
      toast.success(`Frame ${newFrames.length} captured`);
      
      if (newFrames.length >= settings.frames) {
        toast.success('Ready to process!');
      }
    }
  };

  const completeCaptureAndProcess = (frames) => {
    setCapturing(false);
    
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance("Processing your panorama");
      speechSynthesis.speak(utterance);
    }
    
    toast.loading('Creating professional panorama...', { id: 'stitch' });
    setTimeout(() => stitchProfessionalPanorama(frames), 500);
  };

  // Professional panorama stitching with blending
  const stitchProfessionalPanorama = async (frames) => {
    try {
      const panoCanvas = document.createElement('canvas');
      const ctx = panoCanvas.getContext('2d', { alpha: false });

      // Set professional 2:1 aspect ratio
      const targetWidth = settings.width;
      const targetHeight = settings.height;
      panoCanvas.width = targetWidth;
      panoCanvas.height = targetHeight;

      // Fill with black background
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, targetWidth, targetHeight);

      const frameWidth = targetWidth / frames.length;
      const blendWidth = frameWidth * 0.1; // 10% overlap for blending

      for (let i = 0; i < frames.length; i++) {
        const img = await createImageBitmap(frames[i]);
        const x = i * frameWidth;

        // Draw main frame
        ctx.drawImage(img, x, 0, frameWidth, targetHeight);

        // Blend edges if not first or last frame
        if (i > 0) {
          const gradient = ctx.createLinearGradient(x, 0, x + blendWidth, 0);
          gradient.addColorStop(0, 'rgba(0,0,0,1)');
          gradient.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.globalCompositeOperation = 'destination-out';
          ctx.fillStyle = gradient;
          ctx.fillRect(x, 0, blendWidth, targetHeight);
          ctx.globalCompositeOperation = 'source-over';
        }
      }

      // Apply final sharpening pass
      if (aiEnhancement) {
        const imageData = ctx.getImageData(0, 0, targetWidth, targetHeight);
        sharpenImage(imageData);
        ctx.putImageData(imageData, 0, 0);
      }

      // Export with metadata
      panoCanvas.toBlob((blob) => {
        if (blob) {
          const metadata = {
            captureMode: mode,
            quality: captureQuality,
            frameCount: frames.length,
            aiEnhanced: aiEnhancement,
            stabilized: autoStabilization,
            room: currentRoom,
            propertyType: propertyType,
            timestamp: new Date().toISOString()
          };

          const file = new File(
            [blob], 
            `${currentRoom || 'room'}_360_pro.jpg`, 
            { type: 'image/jpeg' }
          );
          
          // Attach metadata
          file.metadata = metadata;

          toast.success('Professional panorama ready!', { id: 'stitch' });
          onCapture(file);
          stopCamera();
        }
      }, 'image/jpeg', settings.quality);

    } catch (error) {
      console.error('Stitching error:', error);
      toast.error('Processing failed. Try again.', { id: 'stitch' });
    }
  };

  // Sharpening filter
  const sharpenImage = (imageData) => {
    const data = imageData.data;
    const width = imageData.width;
    const kernel = [-1, -1, -1, -1, 9, -1, -1, -1, -1];
    const kernelSize = 3;
    const halfKernel = Math.floor(kernelSize / 2);

    const original = new Uint8ClampedArray(data);

    for (let y = halfKernel; y < imageData.height - halfKernel; y++) {
      for (let x = halfKernel; x < width - halfKernel; x++) {
        for (let c = 0; c < 3; c++) {
          let sum = 0;
          for (let ky = 0; ky < kernelSize; ky++) {
            for (let kx = 0; kx < kernelSize; kx++) {
              const px = x + kx - halfKernel;
              const py = y + ky - halfKernel;
              const idx = (py * width + px) * 4 + c;
              sum += original[idx] * kernel[ky * kernelSize + kx];
            }
          }
          const idx = (y * width + x) * 4 + c;
          data[idx] = clamp(sum);
        }
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      {/* Pro Header */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black via-black/80 to-transparent p-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-white text-xl font-bold flex items-center gap-2">
              <span className="text-2xl">📸</span>
              Professional 360° Camera
            </h2>
            <input
              type="text"
              placeholder="Room name (e.g., Master Bedroom)"
              value={currentRoom}
              onChange={(e) => setCurrentRoom(e.target.value)}
              className="mt-2 bg-white/10 text-white px-3 py-1 rounded text-sm border border-white/20 focus:border-purple-500 outline-none"
            />
          </div>
          <button
            onClick={() => {
              stopCamera();
              onClose();
            }}
            className="text-white text-3xl hover:text-red-400 transition-colors"
          >
            ×
          </button>
        </div>
      </div>

      {/* Video Feed with Overlays */}
      <div className="flex-1 relative">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        <canvas ref={canvasRef} className="hidden" />

        {/* Grid Overlay */}
        {showGrid && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="w-full h-full grid grid-cols-3 grid-rows-3">
              {[...Array(9)].map((_, i) => (
                <div key={i} className="border border-white/10" />
              ))}
            </div>
            {/* Horizon line */}
            <div className="absolute top-1/2 left-0 right-0 h-px bg-yellow-400/50" />
            {/* Center crosshair */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
              <div className="w-8 h-8 border-2 border-green-400 rounded-full" />
            </div>
          </div>
        )}

        {/* Capture Progress */}
        <AnimatePresence>
          {capturing && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex flex-col items-center"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="text-6xl mb-4"
              >
                🔄
              </motion.div>
              <div className="bg-black/80 backdrop-blur-sm rounded-xl p-6 max-w-sm mx-4">
                <div className="text-white text-center mb-3">
                  <p className="font-semibold text-lg mb-1">
                    {mode === 'guided' ? 'Rotate slowly 360°' : 'Capturing...'}
                  </p>
                  <p className="text-sm opacity-80">
                    {capturedFrames.length} / {settings.frames} frames
                  </p>
                </div>
                <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden">
                  <motion.div
                    animate={{ width: `${progress}%` }}
                    className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Orientation HUD */}
        {deviceOrientation && !capturing && cameraActive && (
          <div className="absolute top-24 left-4 bg-black/70 backdrop-blur-sm text-white p-3 rounded-lg text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className="opacity-60">Heading:</span>
              <span className="font-mono font-bold">{Math.round(deviceOrientation.alpha)}°</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="opacity-60">Level:</span>
              <div className={`px-2 py-0.5 rounded ${
                Math.abs(deviceOrientation.beta - 90) < 5 ? 'bg-green-500' : 'bg-yellow-500'
              }`}>
                {Math.abs(deviceOrientation.beta - 90) < 5 ? 'GOOD' : 'TILT'}
              </div>
            </div>
          </div>
        )}

        {/* Settings Panel */}
        <div className="absolute top-24 right-4 bg-black/70 backdrop-blur-sm rounded-lg p-3 text-white text-xs space-y-2">
          <button
            onClick={() => setAiEnhancement(!aiEnhancement)}
            className={`w-full px-2 py-1 rounded ${aiEnhancement ? 'bg-purple-600' : 'bg-white/20'}`}
          >
            {aiEnhancement ? '✓' : '○'} AI Enhance
          </button>
          <button
            onClick={() => setAutoStabilization(!autoStabilization)}
            className={`w-full px-2 py-1 rounded ${autoStabilization ? 'bg-purple-600' : 'bg-white/20'}`}
          >
            {autoStabilization ? '✓' : '○'} Stabilize
          </button>
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`w-full px-2 py-1 rounded ${showGrid ? 'bg-purple-600' : 'bg-white/20'}`}
          >
            {showGrid ? '✓' : '○'} Grid
          </button>
        </div>
      </div>

      {/* Pro Controls */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/90 to-transparent p-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {/* Mode Selection */}
          <div className="flex gap-2 justify-center mb-4">
            {[
              { id: 'guided', label: 'Guided', icon: '🎯' },
              { id: 'auto', label: 'Auto', icon: '🤖' },
              { id: 'manual', label: 'Manual', icon: '👆' }
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  mode === m.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-white/10 text-white/60'
                }`}
              >
                {m.icon} {m.label}
              </button>
            ))}
          </div>

          {/* Quality Selector */}
          <div className="flex gap-2 justify-center text-xs">
            {Object.keys(QUALITY_SETTINGS).map((q) => (
              <button
                key={q}
                onClick={() => setCaptureQuality(q)}
                className={`px-3 py-1 rounded uppercase ${
                  captureQuality === q
                    ? 'bg-yellow-500 text-black font-bold'
                    : 'bg-white/10 text-white/60'
                }`}
              >
                {q}
              </button>
            ))}
          </div>

          {/* Capture Button */}
          {mode !== 'manual' ? (
            <button
              onClick={mode === 'guided' ? startGuidedCapture : startAutoCapture}
              disabled={capturing || !cameraActive}
              className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-red-600 text-white font-bold py-4 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-all"
            >
              {capturing ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Capturing {capturedFrames.length}/{settings.frames}...
                </span>
              ) : (
                <span className="text-lg">
                  {mode === 'guided' ? '🎯 Start Guided Capture' : '🤖 Start Auto Capture'}
                </span>
              )}
            </button>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={captureManualFrame}
                disabled={!cameraActive}
                className="bg-purple-600 text-white font-semibold py-4 rounded-xl disabled:opacity-50"
              >
                📸 Capture Frame ({capturedFrames.length})
              </button>
              <button
                onClick={() => completeCaptureAndProcess(capturedFrames)}
                disabled={capturedFrames.length < 12}
                className="bg-green-600 text-white font-semibold py-4 rounded-xl disabled:opacity-50"
              >
                ✓ Process ({capturedFrames.length})
              </button>
            </div>
          )}

          {/* Frame Preview */}
          {capturedFrames.length > 0 && (
            <div className="flex gap-1 overflow-x-auto pb-2 scrollbar-hide">
              {capturedFrames.slice(-12).map((_, i) => (
                <div
                  key={i}
                  className="w-12 h-12 bg-green-500/20 rounded flex-shrink-0 flex items-center justify-center text-white text-xs border border-green-500"
                >
                  ✓
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProCamera360;
