import axios from 'axios';
import Cookies from 'js-cookie';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = Cookies.get('token');
  console.log('API Request - Token present:', !!token, token ? `(${token.substring(0, 20)}...)` : '(none)');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Don't immediately log out - check if we're in the middle of a draft
      // This prevents logout when token expires during auto-pick
      const currentPath = window.location.pathname;
      const isDraftPage = currentPath.includes('/draft');
      
      if (isDraftPage) {
        // In draft, show a warning but don't force logout
        // The user can manually refresh or the page will handle it
        console.warn('Authentication failed during draft. You may need to refresh the page.');
        // Still remove the token so subsequent requests don't keep failing
        Cookies.remove('token');
        // Show a non-blocking notification instead of redirecting
        if (typeof window !== 'undefined' && !document.getElementById('auth-warning')) {
          const warning = document.createElement('div');
          warning.id = 'auth-warning';
          warning.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #ef4444; color: white; padding: 12px 20px; border-radius: 8px; z-index: 10000; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
          warning.innerHTML = 'Session expired. Please refresh the page to continue.';
          document.body.appendChild(warning);
          setTimeout(() => {
            if (warning.parentNode) {
              warning.parentNode.removeChild(warning);
            }
          }, 10000);
        }
        return Promise.reject(error);
      } else {
        // Not in draft, normal logout behavior
        Cookies.remove('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
