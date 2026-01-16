'use client';

import { useState, useEffect } from 'react';
import Cookies from 'js-cookie';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Check if token exists
    const token = Cookies.get('token');
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  const checkAuth = () => {
    const token = Cookies.get('token');
    setIsAuthenticated(!!token);
    return !!token;
  };

  return { isAuthenticated, loading, checkAuth };
}