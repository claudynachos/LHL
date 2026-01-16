'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  requireAuth?: boolean;
  hideInDraft?: boolean;
  showWhenStatus?: string[];
}

const mainNavItems: NavItem[] = [
  { href: '/', label: 'Overview', icon: <HomeIcon />, requireAuth: false },
  { href: '/simulation/new', label: 'New Simulation', icon: <PlusIcon />, requireAuth: true },
  { href: '/admin', label: 'Admin', icon: <SettingsIcon />, requireAuth: true },
];

const simulationNavItems = (simulationId: string): NavItem[] => [
  { href: `/simulation/${simulationId}`, label: 'Dashboard', icon: <HomeIcon />, requireAuth: true },
  { href: `/simulation/${simulationId}/lines`, label: 'Lines', icon: <LinesIcon />, requireAuth: true, hideInDraft: true },
  { href: `/simulation/${simulationId}/standings`, label: 'Standings', icon: <TrophyIcon />, requireAuth: true },
  { href: `/simulation/${simulationId}/stats`, label: 'Stats', icon: <StatsIcon />, requireAuth: true },
  { href: `/simulation/${simulationId}/hall-of-fame`, label: 'Hall of Fame', icon: <HallOfFameIcon />, requireAuth: true },
  { href: `/simulation/${simulationId}/playoffs`, label: 'Playoffs', icon: <PlayoffsIcon />, requireAuth: true, showWhenStatus: ['playoffs'] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { isAuthenticated, loading } = useAuth();
  const [simulationStatus, setSimulationStatus] = useState<string | null>(null);
  
  // Check if we're on a simulation page
  const simulationMatch = pathname?.match(/^\/simulation\/([^\/]+)/);
  const simulationId = simulationMatch ? simulationMatch[1] : null;
  
  // Fetch simulation status if we're on a simulation page
  useEffect(() => {
    if (simulationId && isAuthenticated) {
      api.get(`/api/simulations/${simulationId}`)
        .then(response => {
          setSimulationStatus(response.data.simulation.status);
        })
        .catch(() => {
          // If we can't fetch, assume not in draft
          setSimulationStatus(null);
        });
    } else {
      setSimulationStatus(null);
    }
  }, [simulationId, isAuthenticated]);
  
  const allNavItems = simulationId ? simulationNavItems(simulationId) : mainNavItems;
  
  // Filter nav items based on auth status and draft status
  const navItems = loading ? [] : allNavItems.filter(item => {
    if (item.requireAuth === false) return true; // Public items always show
    if (item.requireAuth === undefined || item.requireAuth === true) {
      if (!isAuthenticated) return false; // Auth-required items only show when logged in
      
      // Hide items that should be hidden during draft
      if (item.hideInDraft && simulationStatus === 'draft') {
        return false;
      }

      if (item.showWhenStatus && simulationStatus && !item.showWhenStatus.includes(simulationStatus)) {
        return false;
      }
    }
    return true;
  });

  // Check if we're in draft mode (for disabling links)
  const isInDraft = simulationStatus === 'draft';
  const isOnDraftPage = pathname?.includes('/draft');

  // Don't show sidebar content if loading
  if (loading) {
    return (
      <div className="w-64 bg-dark-surface border-r border-dark-border min-h-screen flex flex-col">
        <div className="p-6 border-b border-dark-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-orange flex items-center justify-center text-white font-bold text-lg">
              L
            </div>
            <span className="text-xl font-bold text-dark-text">LHL</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-64 bg-dark-surface border-r border-dark-border min-h-screen flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-dark-border">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-full bg-gradient-orange flex items-center justify-center text-white font-bold text-lg group-hover:scale-105 transition-transform">
            L
          </div>
          <span className="text-xl font-bold text-dark-text">LHL</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          // Determine if this item is active
          let isActive = false;
          
          // For Dashboard, only match exact path (not sub-pages like /lines, /stats, etc.)
          if (item.href === `/simulation/${simulationId}`) {
            // Dashboard: only active if exactly on the dashboard page (no sub-path after simulation ID)
            isActive = pathname === item.href;
          } else if (item.href === '/') {
            // Home page: exact match only
            isActive = pathname === item.href;
          } else {
            // Other pages: match exact path or if pathname starts with the href
            isActive = pathname === item.href || 
              (item.href !== '/' && pathname?.startsWith(item.href));
          }
          
          // Disable navigation to Stats, Standings, etc. during draft (unless already on that page)
          const isDraftRestricted = isInDraft && !isOnDraftPage && 
            (item.href.includes('/stats') || item.href.includes('/standings'));
          
          if (isDraftRestricted) {
            return (
              <div
                key={item.href}
                className="sidebar-item opacity-50 cursor-not-allowed"
                title="Draft in progress - navigation disabled"
              >
                {item.icon}
                <span>{item.label}</span>
              </div>
            );
          }
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={isActive ? 'sidebar-item-active' : 'sidebar-item'}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

// Simple SVG Icons
function HomeIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function StatsIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}

function TrophyIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
    </svg>
  );
}

function LinesIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function PlayoffsIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 4h8M6 8h12M4 12h16M6 16h12M8 20h8" />
    </svg>
  );
}

function HallOfFameIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  );
}
