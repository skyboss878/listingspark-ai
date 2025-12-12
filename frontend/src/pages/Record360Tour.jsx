import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api';
import toast from 'react-hot-toast';
import { Camera, Mic, Video, AlertCircle, CheckCircle, Navigation } from 'lucide-react';

const Record360Tour = () => {
  const { listingId } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recording, setRecording] = useState(false);
  const [stream, setStream] = useState(null);
  const [aiGuidance, setAiGuidance] = useState('');
  const [currentRoom, setCurrentRoom] = useState('');
  const [roomsCompleted, setRoomsCompleted] = useState([]);
  const [recordedChunks, setRecordedChunks] = useState([]);
  const [voiceNarration, setVoiceNarration] = useState(true);
  const [tourProgress, setTourProgress] = useState(0);
  const [processing, setProcessing] = useState(false);

  const rooms = [
    { id: 'entrance', name: 'Entrance/Foyer', icon: '🚪' },
    { id: 'living_room', name: 'Living Room', icon: '🛋️' },
    { id: 'kitchen', name: 'Kitchen', icon: '🍳' },
    { id: 'dining_room', name: 'Dining Room', icon: '🍽️' },
    { id: 'master_bedroom', name: 'Master Bedroom', icon: '🛏️' },
    { id: 'bathroom', name: 'Bathroom', icon: '🚿' },
    { id: 'backyard', name: 'Backyard/Outdoor', icon: '🌳' },
    { id: 'garage', name: 'Garage', icon: '🚗' }
  ];

  const [permissionState, setPermissionState] = useState('prompt'); // 'prompt', 'granted', 'denied'
  const [permissionRequested, setPermissionRequested] = useState(false);

  useEffect(() => {
    fetchListing();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [listingId]);

  const fetchListing = async () => {
    try {
      const response = await api.get(`/listings/${listingId}`);
      setListing(response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to load listing');
      navigate('/dashboard');
    }
  };

  const requestCameraPermissions = async () => {
    setPermissionRequested(true);
    setPermissionState('requesting');
    
    try {
      // Request permissions - this will trigger browser's permission dialog
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: true
      });
      
      // Success!
      setStream(mediaStream);
      setPermissionState('granted');
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      
      toast.success('Camera access granted! Ready to record.', { duration: 2000 });
    } catch (error) {
      console.error('Camera permission error:', error);
      setPermissionState('denied');
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        toast.error('Camera permission denied. Please enable camera access in your browser settings.', { duration: 5000 });
      } else if (error.name === 'NotFoundError') {
        toast.error('No camera found on this device.', { duration: 5000 });
      } else {
        toast.error('Failed to access camera. Please check your browser settings.', { duration: 5000 });
      }
    }
  };

  const startRoomRecording = async (room) => {
    if (!stream) {
      toast.error('Camera not ready');
      return;
    }

    setCurrentRoom(room.name);
    setRecording(true);

    // Get AI guidance for this room
    try {
      const response = await api.post(`/360tour/start-room/${listingId}`, {
        room_type: room.id,
        property_type: listing?.property_type || 'single_family'
      });
      setAiGuidance(response.data.initial_guidance || 'Start by panning slowly from left to right...');
    } catch (error) {
      setAiGuidance('Start by panning slowly from left to right, capturing all details...');
    }

    // Start recording
    const chunks = [];
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'video/webm;codecs=vp9'
    });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'video/webm' });
      setRecordedChunks(prev => [...prev, { room: room.id, blob }]);
      setRoomsCompleted(prev => [...prev, room.id]);
      setTourProgress(((roomsCompleted.length + 1) / rooms.length) * 100);
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();

    // Simulate AI guidance updates
    let guidanceInterval = setInterval(async () => {
      try {
        const response = await api.post(`/360tour/get-guidance/${listingId}`, {
          room_type: room.id,
          duration: Math.floor(Date.now() / 1000)
        });
        setAiGuidance(response.data.guidance || aiGuidance);
      } catch (error) {
        // Use fallback guidance
        const fallbackGuidance = [
          'Pan slowly to the right...',
          'Capture the ceiling details...',
          'Focus on key features...',
          'Show the floor and fixtures...',
          'Almost done, pan back to center...'
        ];
        const randomGuidance = fallbackGuidance[Math.floor(Math.random() * fallbackGuidance.length)];
        setAiGuidance(randomGuidance);
      }
    }, 8000);

    // Store interval for cleanup
    mediaRecorderRef.current.guidanceInterval = guidanceInterval;
  };

  const stopRoomRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      if (mediaRecorderRef.current.guidanceInterval) {
        clearInterval(mediaRecorderRef.current.guidanceInterval);
      }
    }
    setRecording(false);
    setCurrentRoom('');
    setAiGuidance('');
    toast.success('Room recorded! Select next room or complete tour.');
  };

  const completeTour = async () => {
    if (recordedChunks.length === 0) {
      toast.error('Please record at least one room');
      return;
    }

    setProcessing(true);
    toast.loading('Processing your 360° tour...', { id: 'processing' });

    try {
      // Upload each room video
      const formData = new FormData();
      recordedChunks.forEach((chunk, index) => {
        formData.append(`room_${chunk.room}`, chunk.blob, `${chunk.room}.webm`);
      });
      formData.append('listing_id', listingId);
      formData.append('enable_narration', voiceNarration);
      formData.append('property_type', listing?.property_type || 'single_family');

      const response = await api.post(`/360tour/process/${listingId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000 // 5 minutes
      });

      toast.success('✅ 360° Tour created with AI narration!', { id: 'processing' });
      navigate(`/virtual-tour/${listingId}`);
    } catch (error) {
      toast.error('Failed to process tour. Please try again.', { id: 'processing' });
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-400 border-t-transparent rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-xl">Loading listing...</p>
        </div>
      </div>
    );
  }

  // Show permission request screen
  if (!permissionRequested || permissionState === 'denied') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/10 backdrop-blur-sm rounded-xl p-8 border border-white/20 max-w-md text-center"
        >
          <Camera className="w-20 h-20 mx-auto mb-6 text-purple-400" />
          <h2 className="text-3xl font-bold mb-4">Camera Access Required</h2>
          <p className="text-purple-200 mb-6">
            To record your 360° tour with AI guidance, we need access to your camera and microphone.
          </p>
          
          {permissionState === 'denied' && (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-6">
              <AlertCircle className="w-6 h-6 mx-auto mb-2 text-red-400" />
              <p className="text-sm text-red-200">
                Camera access was denied. Please enable camera permissions in your browser settings and refresh the page.
              </p>
            </div>
          )}

          <div className="space-y-3 mb-6">
            <button
              onClick={requestCameraPermissions}
              disabled={permissionState === 'requesting'}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 px-8 py-4 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50"
            >
              {permissionState === 'requesting' ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Requesting Permission...
                </span>
              ) : (
                '📷 Enable Camera & Microphone'
              )}
            </button>
            
            <button
              onClick={() => navigate(`/listing/${listingId}`)}
              className="w-full bg-gray-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-700 transition-all"
            >
              Cancel
            </button>
          </div>

          <div className="text-left bg-purple-600/20 rounded-lg p-4">
            <p className="text-sm text-purple-200 font-semibold mb-2">Why we need this:</p>
            <ul className="text-xs text-purple-100 space-y-1">
              <li>• 📹 Camera: Record 360° property tours</li>
              <li>• 🎤 Microphone: Capture audio for narration</li>
              <li>• 🔒 Your privacy is protected - recordings stay on your device until you upload</li>
            </ul>
          </div>
        </motion.div>
      </div>
    );
  }

  // Show loading while camera is initializing
  if (permissionState === 'requesting' || (permissionState === 'granted' && !stream)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-400 border-t-transparent rounded-full animate-spin mb-4 mx-auto"></div>
          <p className="text-xl">Initializing camera...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={() => navigate(`/listing/${listingId}`)}
            className="text-white hover:text-purple-300 transition-colors"
          >
            ← Back
          </button>
          <div className="text-center flex-1">
            <h1 className="text-2xl font-bold">🎥 AI-Directed 360° Tour</h1>
            <p className="text-purple-200 text-sm">{listing?.address}</p>
          </div>
          <div className="w-20"></div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Camera View */}
          <div className="lg:col-span-2">
            <div className="bg-black rounded-xl overflow-hidden relative aspect-video">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
              
              {/* Recording Indicator */}
              {recording && (
                <div className="absolute top-4 left-4 flex items-center gap-2 bg-red-600 px-4 py-2 rounded-full animate-pulse">
                  <div className="w-3 h-3 bg-white rounded-full"></div>
                  <span className="font-semibold">REC</span>
                </div>
              )}

              {/* AI Guidance Overlay */}
              <AnimatePresence>
                {aiGuidance && recording && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="absolute bottom-4 left-4 right-4 bg-gradient-to-r from-purple-600/90 to-pink-600/90 backdrop-blur-sm rounded-lg p-4 border border-white/20"
                  >
                    <div className="flex items-start gap-3">
                      <Navigation className="w-6 h-6 text-white flex-shrink-0 mt-1 animate-pulse" />
                      <div>
                        <p className="font-semibold text-sm mb-1">🤖 AI Director:</p>
                        <p className="text-lg">{aiGuidance}</p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Current Room Label */}
              {currentRoom && (
                <div className="absolute top-4 right-4 bg-purple-600/90 backdrop-blur-sm px-4 py-2 rounded-full">
                  <span className="font-semibold">{currentRoom}</span>
                </div>
              )}
            </div>

            {/* Recording Controls */}
            <div className="mt-4 flex gap-4">
              {!recording ? (
                <button
                  onClick={completeTour}
                  disabled={recordedChunks.length === 0 || processing}
                  className="flex-1 bg-gradient-to-r from-green-500 to-emerald-500 px-6 py-4 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processing ? '⏳ Processing...' : `✅ Complete Tour (${recordedChunks.length} rooms)`}
                </button>
              ) : (
                <button
                  onClick={stopRoomRecording}
                  className="flex-1 bg-red-600 px-6 py-4 rounded-lg font-semibold hover:bg-red-700 transition-all"
                >
                  ⏹️ Stop Recording
                </button>
              )}
            </div>

            {/* Settings */}
            <div className="mt-4 bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
              <h3 className="font-semibold mb-3">Tour Settings</h3>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mic className="w-5 h-5" />
                  <span>AI Voice Narration</span>
                </div>
                <button
                  onClick={() => setVoiceNarration(!voiceNarration)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    voiceNarration ? 'bg-green-500' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      voiceNarration ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Room Selection */}
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
            <h2 className="text-xl font-bold mb-4">📋 Record Rooms</h2>
            <p className="text-sm text-purple-200 mb-4">
              Select a room to start recording. AI will guide you through capturing the best footage.
            </p>

            {/* Progress Bar */}
            <div className="mb-6">
              <div className="flex justify-between text-sm mb-2">
                <span>Progress</span>
                <span>{Math.round(tourProgress)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all"
                  style={{ width: `${tourProgress}%` }}
                ></div>
              </div>
            </div>

            {/* Rooms List */}
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {rooms.map((room) => {
                const isCompleted = roomsCompleted.includes(room.id);
                const isCurrent = currentRoom === room.name;
                
                return (
                  <button
                    key={room.id}
                    onClick={() => !recording && startRoomRecording(room)}
                    disabled={recording && !isCurrent}
                    className={`w-full flex items-center justify-between p-4 rounded-lg transition-all ${
                      isCurrent
                        ? 'bg-red-600'
                        : isCompleted
                        ? 'bg-green-600/50'
                        : 'bg-white/5 hover:bg-white/10'
                    } ${recording && !isCurrent ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{room.icon}</span>
                      <span className="font-medium">{room.name}</span>
                    </div>
                    {isCompleted ? (
                      <CheckCircle className="w-5 h-5 text-green-300" />
                    ) : isCurrent ? (
                      <Video className="w-5 h-5 animate-pulse" />
                    ) : (
                      <Camera className="w-5 h-5" />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Instructions */}
            <div className="mt-6 p-4 bg-purple-600/20 rounded-lg border border-purple-400/30">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-purple-300 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-purple-100">
                  <p className="font-semibold mb-1">Tips:</p>
                  <ul className="space-y-1 text-xs">
                    <li>• Hold phone steady in landscape mode</li>
                    <li>• Follow AI director's instructions</li>
                    <li>• Pan slowly for best results</li>
                    <li>• Ensure good lighting in each room</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Record360Tour;
