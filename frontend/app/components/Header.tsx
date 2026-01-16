'use client';

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import Cookies from 'js-cookie';
import { useAuth } from '@/lib/auth';

export default function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, loading } = useAuth();
  const [username, setUsername] = useState<string>('U');
  
  // Check if we're on a simulation page
  const isInSimulation = pathname?.startsWith('/simulation/');

  useEffect(() => {
    // Get username from token or cookies if available
    const token = Cookies.get('token');
    if (token) {
      try {
        // Decode token to get username (simple base64 decode of JWT payload)
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.sub) {
          // Try to get username from sub or get first letter
          setUsername(payload.sub.charAt(0).toUpperCase());
        }
      } catch (e) {
        // If token decode fails, use default
      }
    }
  }, [isAuthenticated]);

  const handleLogout = () => {
    Cookies.remove('token');
    router.push('/login');
    router.refresh();
  };

  if (loading) {
    return (
      <header className="h-16 bg-dark-surface border-b border-dark-border flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold text-dark-text">
            Legend Hockey League
          </h1>
        </div>
        <div className="w-8 h-8"></div>
      </header>
    );
  }

  return (
    <header className="h-16 bg-dark-surface border-b border-dark-border flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-dark-text">
          Legend Hockey League
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {isAuthenticated ? (
          <>
            {isInSimulation && (
              <Link
                href="/"
                className="px-4 py-2 text-sm text-dark-text-muted hover:text-dark-text transition-colors"
              >
                Home
              </Link>
            )}
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-dark-text-muted hover:text-dark-text transition-colors"
            >
              Logout
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-orange flex items-center justify-center text-white text-sm font-semibold">
              {username}
            </div>
          </>
        ) : (
          <Link
            href="/login"
            className="px-4 py-2 text-sm bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
          >
            Login
          </Link>
        )}
      </div>
    </header>
  );
}
