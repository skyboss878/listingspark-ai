import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API_BASE = `${BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.baseURL = API_BASE;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// API Service
const api = {
  // Users
  users: {
    create: async (email, name) => {
      const response = await axios.post('/users', { email, name });
      return response.data;
    },
  },

  // Properties
  properties: {
    create: async (userId, propertyData) => {
      const response = await axios.post(`/properties?user_id=${userId}`, propertyData);
      return response.data;
    },
    
    getAll: async (userId) => {
      const response = await axios.get(`/properties/${userId}`);
      return response.data;
    },
    
    getById: async (propertyId) => {
      // Note: Backend doesn't have this endpoint yet, we'll get from list
      return null;
    }
  },

  // Virtual Tours
  tours: {
    upload360: async (propertyId, file, sceneName = "Main Room") => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('scene_name', sceneName);
      
      const response = await axios.post(
        `/properties/${propertyId}/upload-360`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );
      return response.data;
    },
    
    getPropertyTours: async (propertyId) => {
      const response = await axios.get(`/properties/${propertyId}/tours`);
      return response.data;
    },
    
    trackView: async (tourId) => {
      const response = await axios.post(`/tours/${tourId}/view`);
      return response.data;
    },
    
    getTourUrl: (tourId) => {
      return `${BACKEND_URL}/tours/${tourId}/tour.html`;
    }
  },

  // Viral Content
  viralContent: {
    generate: async (propertyId) => {
      const response = await axios.post(`/properties/${propertyId}/viral-content`);
      return response.data;
    },
    
    get: async (propertyId) => {
      const response = await axios.get(`/properties/${propertyId}/viral-content`);
      return response.data;
    }
  },

  // Analytics
  analytics: {
    get: async (propertyId) => {
      const response = await axios.get(`/properties/${propertyId}/analytics`);
      return response.data;
    }
  },

  // Dashboard
  dashboard: {
    get: async (userId) => {
      const response = await axios.get(`/dashboard/${userId}`);
      return response.data;
    }
  },

  // Health Check
  health: async () => {
    const response = await axios.get('/health');
    return response.data;
  }
};

// Error handler
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

export default api;
export { BACKEND_URL, API_BASE };
