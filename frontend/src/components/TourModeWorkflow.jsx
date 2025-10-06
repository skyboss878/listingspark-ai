import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import ProCamera360 from './ProCamera360';
import toast from 'react-hot-toast';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL + '/api' || 'http://localhost:8000/api';

// Professional room templates for different property types
const PROPERTY_TEMPLATES = {
  house: {
    name: "Single Family Home",
    rooms: [
      { name: "Front Exterior", type: "exterior", tips: "Capture the curb appeal, front door, and landscaping", icon: "🏠" },
      { name: "Foyer/Entry", type: "entry", tips: "Show the welcoming entrance and flow", icon: "🚪" },
      { name: "Living Room", type: "living", tips: "Highlight space, natural light, and focal points", icon: "🛋️" },
      { name: "Kitchen", type: "kitchen", tips: "Show appliances, counters, and flow to dining", icon: "🍳" },
      { name: "Dining Room", type: "dining", tips: "Capture the entertaining space", icon: "🍽️" },
      { name: "Master Bedroom", type: "bedroom", tips: "Show size, natural light, and closet space", icon: "🛏️" },
      { name: "Master Bathroom", type: "bathroom", tips: "Highlight fixtures, shower, and finishes", icon: "🚿" },
      { name: "Additional Bedrooms", type: "bedroom", tips: "Show versatility and size", icon: "🛏️", optional: true },
      { name: "Backyard", type: "exterior", tips: "Capture outdoor living space and potential", icon: "🌳" },
      { name: "Garage", type: "utility", tips: "Show storage and parking", icon: "🚗", optional: true }
    ]
  },
  apartment: {
    name: "Apartment/Condo",
    rooms: [
      { name: "Building Exterior", type: "exterior", tips: "Show building facade and entrance", icon: "🏢" },
      { name: "Entry/Hallway", type: "entry", tips: "Capture the welcome", icon: "🚪" },
      { name: "Living Area", type: "living", tips: "Show open concept and flow", icon: "🛋️" },
      { name: "Kitchen", type: "kitchen", tips: "Highlight modern appliances", icon: "🍳" },
      { name: "Master Bedroom", type: "bedroom", tips: "Show spaciousness", icon: "🛏️" },
      { name: "Bathroom", type: "bathroom", tips: "Highlight finishes", icon: "🚿" },
      { name: "Balcony/Patio", type: "exterior", tips: "Show outdoor space and views", icon: "🌇", optional: true }
    ]
  },
  commercial: {
    name: "Commercial Property",
    rooms: [
      { name: "Street View", type: "exterior", tips: "Show visibility and access", icon: "🏪" },
      { name: "Main Entrance", type: "entry", tips: "Professional first impression", icon: "🚪" },
      { name: "Reception/Lobby", type: "commercial", tips: "Showcase professional space", icon: "💼" },
      { name: "Main Floor Area", type: "commercial", tips: "Show usable square footage", icon: "📊" },
      { name: "Private Offices", type: "commercial", tips: "Demonstrate flexibility", icon: "🖥️", optional: true },
      { name: "Conference Room", type: "commercial", tips: "Show collaboration spaces", icon: "👥", optional: true },
      { name: "Parking", type: "exterior", tips: "Highlight parking availability", icon: "🅿️" }
    ]
  },
  luxury: {
    name: "Luxury Estate",
    rooms: [
      { name: "Grand Entrance", type: "exterior", tips: "Capture the impressive approach", icon: "🏰" },
      { name: "Foyer", type: "entry", tips: "Showcase architectural details", icon: "✨" },
      { name: "Living/Great Room", type: "living", tips: "Highlight volume and elegance", icon: "🛋️" },
      { name: "Gourmet Kitchen", type: "kitchen", tips: "Show high-end appliances and finishes", icon: "👨‍🍳" },
      { name: "Formal Dining", type: "dining", tips: "Capture entertaining potential", icon: "🍷" },
      { name: "Master Suite", type: "bedroom", tips: "Show luxury and privacy", icon: "🛏️" },
      { name: "Spa Bathroom", type: "bathroom", tips: "Highlight premium fixtures", icon: "💎" },
      { name: "Home Theater", type: "entertainment", tips: "Show unique amenities", icon: "🎬", optional: true },
      { name: "Wine Cellar", type: "entertainment", tips: "Highlight special features", icon: "🍾", optional: true },
      { name: "Pool/Outdoor Living", type: "exterior", tips: "Capture resort-style amenities", icon: "🏊" },
      { name: "Guest House", type: "additional", tips: "Show additional living spaces", icon: "🏡", optional: true }
    ]
  }
};

const TourModeWorkflow = () => {
  const { propertyId } = useParams();
  const navigate = useNavigate();
  
  const [propertyData, setPropertyData] = useState(null);
  const [propertyType, setPropertyType] = useState('house');
  const [currentRoomIndex, setCurrentRoomIndex] = useState(0);
  const [capturedRooms, setCapturedRooms] = useState([]);
  const [showCamera, setShowCamera] = useState(false);
  const [tourProgress, setTourProgress] = useState(0);
  const [tourStarted, setTourStarted] = useState(false);
  const [processing, setProcessing] = useState(false);

  const template = PROPERTY_TEMPLATES[propertyType];
  const currentRoom = template.rooms[currentRoomIndex];
  const totalRooms = template.rooms.length;
  const requiredRooms = template.rooms.filter(r => !r.optional).length;

  useEffect(() => {
    if (propertyId) {
      loadPropertyData();
    }
  }, [propertyId]);

  useEffect(() => {
    setTourProgress((capturedRooms.length / totalRooms) * 100);
  }, [capturedRooms, totalRooms]);

  const loadPropertyData = async () => {
    try {
      const response = await axios.get(`${API}/properties/${propertyId}`);
      setPropertyData(response.data);
      setPropertyType(response.data.property_type || 'house');
    } catch (error) {
      console.error('Error loading property:', error);
      toast.error('Failed to load property data');
    }
  };

  const startTour = () => {
    setTourStarted(true);
    setShowCamera(true);
    
    // Voice guidance if available
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(
        `Let's start with the ${currentRoom.name}. ${currentRoom.tips}`
      );
      speechSynthesis.speak(utterance);
    }
    
    toast.success(`Starting with: ${currentRoom.name}`, { duration: 3000 });
  };

  const handleRoomCaptured = async (imageFile) => {
    try {
      // Upload image to backend with AI enhancement
      const formData = new FormData();
      formData.append('image', imageFile);
      formData.append('room_name', currentRoom.name);
      formData.append('room_type', currentRoom.type);
      formData.append('property_id', propertyId);
      formData.append('enhance', 'true');

      toast.loading('Enhancing image...', { id: 'upload' });

      const response = await axios.post(
        `${API}/properties/${propertyId}/upload-room-360`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      const roomData = {
        ...currentRoom,
        index: currentRoomIndex,
        imageId: response.data.room_id,
        imageUrl: response.data.image_url,
        capturedAt: new Date().toISOString()
      };

      setCapturedRooms([...capturedRooms, roomData]);
      toast.success(`${currentRoom.name} captured!`, { id: 'upload' });

      // Auto-advance to next room
      if (currentRoomIndex < totalRooms - 1) {
        setTimeout(() => {
          setCurrentRoomIndex(currentRoomIndex + 1);
          setShowCamera(true);
          
          const nextRoom = template.rooms[currentRoomIndex + 1];
          if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(
              `Great! Now let's capture the ${nextRoom.name}. ${nextRoom.tips}`
            );
            speechSynthesis.speak(utterance);
          }
          
          toast(`Next: ${nextRoom.name}`, { icon: nextRoom.icon });
        }, 1500);
      } else {
        // All rooms captured
        toast.success('All rooms captured! Processing tour...');
        processTour();
      }

    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload. Try again.', { id: 'upload' });
      setShowCamera(true);
    }
  };

  const skipRoom = () => {
    if (currentRoom.optional) {
      toast('Skipped optional room', { icon: '⏭️' });
      
      if (currentRoomIndex < totalRooms - 1) {
        setCurrentRoomIndex(currentRoomIndex + 1);
      } else {
        checkTourCompletion();
      }
    } else {
      toast.error('This room is required for a complete tour');
    }
  };

  const retakeRoom = (roomIndex) => {
    setCurrentRoomIndex(roomIndex);
    setCapturedRooms(capturedRooms.filter((_, i) => i !== roomIndex));
    setShowCamera(true);
  };

  const checkTourCompletion = () => {
    const capturedRequired = capturedRooms.filter(r => !r.optional).length;
    
    if (capturedRequired >= requiredRooms) {
      toast.success('Tour complete! Processing...');
      processTour();
    } else {
      toast.error(`Need ${requiredRooms - capturedRequired} more required rooms`);
    }
  };

  const processTour = async () => {
    setProcessing(true);
    
    try {
      // Generate complete 360° tour with narration
      const response = await axios.post(
        `${API}/properties/${propertyId}/generate-complete-tour`,
        {
          rooms: capturedRooms,
          voice_narration: true,
          add_music: true,
          property_type: propertyType
        }
      );

      toast.success('Professional tour created!');
      
      // Navigate to tour preview
      setTimeout(() => {
        navigate(`/virtual-tour/${propertyId}`);
      }, 2000);

    } catch (error) {
      console.error('Tour processing error:', error);
      toast.error('Failed to process tour');
      setProcessing(false);
    }
  };

  if (showCamera) {
    return (
      <ProCamera360
        onCapture={handleRoomCaptured}
        onClose={() => setShowCamera(false)}
        propertyType={propertyType}
      />
    );
  }

  if (processing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center text-white"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="text-8xl mb-6"
          >
            🎬
          </motion.div>
          <h2 className="text-3xl font-bold mb-4">Creating Your Professional Tour</h2>
          <p className="text-xl opacity-80 mb-6">AI Enhancement • Voice Narration • Music</p>
          <div className="w-64 mx-auto bg-white/20 rounded-full h-3 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "100%" }}
              transition={{ duration: 8, ease: "easeInOut" }}
              className="h-full bg-gradient-to-r from-green-400 to-blue-500"
            />
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              🎬 Guided Tour Mode
            </h1>
            <p className="text-purple-200">
              {propertyData?.title || 'Professional Property Tour'}
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 border border-white/30 rounded-lg hover:bg-white/10"
          >
            Exit
          </button>
        </div>

        {/* Progress Bar */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">
              Progress: {capturedRooms.length} / {totalRooms} rooms
            </span>
            <span className="text-sm opacity-80">
              {Math.round(tourProgress)}% Complete
            </span>
          </div>
          <div className="w-full bg-white/20 rounded-full h-4 overflow-hidden">
            <motion.div
              animate={{ width: `${tourProgress}%` }}
              className="h-full bg-gradient-to-r from-green-400 via-blue-500 to-purple-600"
              transition={{ duration: 0.5 }}
            />
          </div>
        </motion.div>

        {!tourStarted ? (
          /* Property Type Selection */
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto"
          >
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
              <h2 className="text-2xl font-bold mb-6">Select Property Type</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                {Object.entries(PROPERTY_TEMPLATES).map(([key, template]) => (
                  <motion.button
                    key={key}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setPropertyType(key)}
                    className={`p-6 rounded-xl text-left transition-all ${
                      propertyType === key
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 border-2 border-white'
                        : 'bg-white/5 border-2 border-white/20 hover:border-white/40'
                    }`}
                  >
                    <h3 className="text-xl font-bold mb-2">{template.name}</h3>
                    <p className="text-sm opacity-80 mb-3">
                      {template.rooms.length} rooms to capture
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {template.rooms.slice(0, 5).map((room, i) => (
                        <span key={i} className="text-2xl">{room.icon}</span>
                      ))}
                      {template.rooms.length > 5 && (
                        <span className="text-sm opacity-60">+{template.rooms.length - 5} more</span>
                      )}
                    </div>
                  </motion.button>
                ))}
              </div>

              <div className="bg-blue-500/20 rounded-xl p-6 mb-6">
                <h3 className="font-bold mb-3 flex items-center gap-2">
                  <span className="text-2xl">💡</span>
                  What You'll Get:
                </h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>Room-by-room guided capture with professional tips</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>AI-enhanced images (auto-brightness, contrast, colors)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>Professional voice narration for each room</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>Seamless 360° virtual tour experience</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>Background music and professional transitions</span>
                  </li>
                </ul>
              </div>

              <button
                onClick={startTour}
                className="w-full bg-gradient-to-r from-green-500 to-blue-600 text-white font-bold py-4 rounded-xl text-xl hover:shadow-2xl transition-all"
              >
                🎬 Start Guided Tour
              </button>
            </div>
          </motion.div>
        ) : (
          /* Room Capture Checklist */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Current Room Instructions */}
            <div className="lg:col-span-2">
              <motion.div
                key={currentRoomIndex}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 mb-6"
              >
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <span className="text-6xl">{currentRoom.icon}</span>
                    <div>
                      <h2 className="text-3xl font-bold mb-2">{currentRoom.name}</h2>
                      {currentRoom.optional && (
                        <span className="bg-yellow-500/20 text-yellow-300 px-3 py-1 rounded-full text-sm">
                          Optional
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="text-4xl font-bold text-white/40">
                    {currentRoomIndex + 1}/{totalRooms}
                  </span>
                </div>

                <div className="bg-blue-500/20 rounded-xl p-6 mb-6">
                  <h3 className="font-bold mb-3 flex items-center gap-2">
                    <span className="text-xl">💡</span>
                    Professional Tips:
                  </h3>
                  <p className="text-lg">{currentRoom.tips}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setShowCamera(true)}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-4 rounded-xl text-lg hover:shadow-xl transition-all"
                  >
                    📸 Capture {currentRoom.name}
                  </button>
                  {currentRoom.optional && (
                    <button
                      onClick={skipRoom}
                      className="border-2 border-white/30 text-white font-semibold py-4 rounded-xl hover:bg-white/10 transition-all"
                    >
                      ⏭️ Skip Room
                    </button>
                  )}
                </div>
              </motion.div>

              {/* Quick Tips */}
              <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-500/30">
                <h3 className="font-bold mb-4 flex items-center gap-2">
                  <span className="text-2xl">🎯</span>
                  Pro Capture Tips:
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Hold phone vertically</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Rotate slowly and smoothly</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Keep phone level</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Ensure good lighting</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Room Checklist Sidebar */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 h-fit sticky top-8">
              <h3 className="font-bold text-lg mb-4">Room Checklist</h3>
              
              <div className="space-y-2">
                {template.rooms.map((room, index) => {
                  const isCaptured = capturedRooms.some(r => r.index === index);
                  const isCurrent = index === currentRoomIndex;
                  
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`p-3 rounded-lg flex items-center justify-between transition-all ${
                        isCaptured
                          ? 'bg-green-500/20 border border-green-500'
                          : isCurrent
                          ? 'bg-purple-500/20 border-2 border-purple-400'
                          : 'bg-white/5 border border-white/10'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{room.icon}</span>
                        <div>
                          <div className="font-medium text-sm">{room.name}</div>
                          {room.optional && (
                            <div className="text-xs opacity-60">Optional</div>
                          )}
                        </div>
                      </div>
                      
                      {isCaptured ? (
                        <button
                          onClick={() => retakeRoom(index)}
                          className="text-xs bg-white/10 px-2 py-1 rounded hover:bg-white/20"
                        >
                          ↻ Retake
                        </button>
                      ) : isCurrent ? (
                        <span className="text-purple-400 text-xl">→</span>
                      ) : (
                        <span className="text-white/20 text-xl">○</span>
                      )}
                    </motion.div>
                  );
                })}
              </div>

              {capturedRooms.length >= requiredRooms && (
                <button
                  onClick={checkTourCompletion}
                 className="w-full mt-6 bg-gradient-to-r from-green-500 to-blue-600 text-white font-bold py-3 rounded-lg hover:shadow-xl transition-all"
                >
                  ✓ Complete Tour ({capturedRooms.length} rooms)
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TourModeWorkflow;
