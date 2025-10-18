import React, { createContext, useState, useEffect } from 'react';
import api from '../utils/api';

export const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      try {
        const response = await api.get('/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('auth_token');
      }
    }
    setLoading(false);
  };

  // Login with username/password
  const login = async (email, password) => {
    const formData = new FormData();
    formData.append('username', email);  // Backend expects 'username'
    formData.append('password', password);

    const response = await api.post('/auth/login-sqlite', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    localStorage.setItem('auth_token', response.data.access_token);
    setUser(response.data.user);
    return response.data;
  };

  // Register new user
  const register = async (userData) => {
    const response = await api.post('/auth/register', userData);
    localStorage.setItem('auth_token', response.data.access_token);
    setUser(response.data.user);
    return response.data;
  };

  // Logout
  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  return (
    <UserContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </UserContext.Provider>
  );
};
