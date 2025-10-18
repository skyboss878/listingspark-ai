import axios from 'axios';

// Detect backend URL (Vite or React)
const BACKEND_URL =
  import.meta?.env?.VITE_API_URL ||
  process.env.REACT_APP_API_URL ||
  'http://localhost:8000';

const API_BASE = `${BACKEND_URL}/api`;

// Global defaults
axios.defaults.baseURL = API_BASE;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Optional: auto-add token from localStorage
axios.interceptors.request.use((config) => {
  const token =
    localStorage.getItem('token') || localStorage.getItem('auth_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default axios;
