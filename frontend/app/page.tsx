'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import DashboardLayout from './components/DashboardLayout';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Simulation } from '@/lib/types';
import { useModal } from './components/ModalContext';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { showAlert, showConfirm } = useModal();
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [quitSimulations, setQuitSimulations] = useState<Simulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [showQuitSims, setShowQuitSims] = useState(false);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      loadSimulations();
    } else if (!authLoading && !isAuthenticated) {
      setLoading(false);
    }
  }, [authLoading, isAuthenticated]);

  const loadSimulations = async () => {
    try {
      const response = await api.get('/api/simulations/');
      setSimulations(response.data.simulations || []);
      setQuitSimulations(response.data.quit_simulations || []);
    } catch (error: any) {
      console.error('Failed to load simulations', error);
      if (error.response?.status === 401) {
        // Token expired or invalid
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (simulationId: number) => {
    const confirmed = await showConfirm('Are you sure you want to delete this simulation? This action cannot be undone.');
    if (!confirmed) {
      return;
    }

    setDeletingId(simulationId);
    try {
      await api.delete(`/api/simulations/${simulationId}`);
      setSimulations(simulations.filter(s => s.id !== simulationId));
      setQuitSimulations(quitSimulations.filter(s => s.id !== simulationId));
    } catch (error: any) {
      console.error('Failed to delete simulation', error);
      await showAlert('Failed to delete simulation. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleQuit = async (simulationId: number) => {
    const confirmed = await showConfirm('Quit this simulation? You can rejoin it later from the quit simulations section.');
    if (!confirmed) {
      return;
    }

    try {
      await api.post(`/api/simulations/${simulationId}/quit`);
      // Move simulation from active to quit list
      const quitSim = simulations.find(s => s.id === simulationId);
      if (quitSim) {
        setSimulations(simulations.filter(s => s.id !== simulationId));
        setQuitSimulations([...quitSimulations, { ...quitSim, is_active: false }]);
      }
    } catch (error: any) {
      console.error('Failed to quit simulation', error);
      await showAlert('Failed to quit simulation. Please try again.');
    }
  };

  const handleRejoin = async (simulationId: number) => {
    try {
      const response = await api.post(`/api/simulations/${simulationId}/rejoin`);
      // Move simulation from quit to active list
      const rejoinedSim = response.data.simulation;
      setQuitSimulations(quitSimulations.filter(s => s.id !== simulationId));
      setSimulations([rejoinedSim, ...simulations]);
    } catch (error: any) {
      console.error('Failed to rejoin simulation', error);
      await showAlert('Failed to rejoin simulation. Please try again.');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'season':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'playoffs':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'completed':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-dark-text-muted">Loading...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-dark-text mb-2">
            {isAuthenticated ? 'Welcome back! 👋' : 'Welcome to LHL! 👋'}
          </h1>
          <p className="text-dark-text-muted text-lg">
            {isAuthenticated 
              ? 'Manage your hockey simulation seasons and track your progress.'
              : 'Start your journey by creating an account and building your dream team.'}
          </p>
        </div>

        {/* Simulations List (only if logged in) */}
        {isAuthenticated && (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-dark-text">Your Simulations</h2>
              <Link
                href="/simulation/new"
                className="btn btn-primary"
              >
                + New Simulation
              </Link>
            </div>

            {simulations.length === 0 && quitSimulations.length === 0 ? (
              <div className="card text-center py-12">
                <div className="w-16 h-16 rounded-full bg-primary-500/20 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-dark-text mb-2">No Simulations Yet</h3>
                <p className="text-dark-text-muted mb-6">Create your first simulation to start building your team!</p>
                <Link href="/simulation/new" className="btn btn-primary">
                  Create Your First Simulation
                </Link>
              </div>
            ) : (
              <>
                {simulations.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    {simulations.map((sim) => (
                      <div key={sim.id} className="card group">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h3 className="text-lg font-semibold text-dark-text mb-1">
                              {sim.name || `Season ${sim.current_season} / ${sim.year_length}`}
                            </h3>
                            <p className="text-sm text-dark-text-muted">
                              {sim.name ? `Season ${sim.current_season} / ${sim.year_length}` : ''} {sim.num_teams} Teams • {new Date(sim.created_at!).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleQuit(sim.id)}
                              className="opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-orange-500/20 rounded-lg text-orange-400"
                              title="Quit simulation"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                            <button
                              onClick={() => handleDelete(sim.id)}
                              disabled={deletingId === sim.id}
                              className="opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-red-500/20 rounded-lg text-red-400 disabled:opacity-50"
                              title="Delete simulation"
                            >
                              {deletingId === sim.id ? (
                                <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin"></div>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              )}
                            </button>
                          </div>
                        </div>

                        <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border mb-4 ${getStatusColor(sim.status)}`}>
                          {sim.status.charAt(0).toUpperCase() + sim.status.slice(1)}
                        </div>

                        <div className="flex items-center gap-4 text-sm text-dark-text-muted mb-4">
                          <span>Date: {sim.current_date}</span>
                        </div>

                        {sim.status === 'draft' ? (
                          <Link
                            href={`/simulation/${sim.id}/draft`}
                            className="btn btn-primary w-full"
                          >
                            Rejoin Draft
                          </Link>
                        ) : (
                          <Link
                            href={`/simulation/${sim.id}`}
                            className="btn btn-secondary w-full"
                          >
                            View Simulation
                          </Link>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Quit Simulations Section */}
                {quitSimulations.length > 0 && (
                  <div className="mt-8">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-2xl font-bold text-dark-text">Quit Simulations</h2>
                      <button
                        onClick={() => setShowQuitSims(!showQuitSims)}
                        className="text-sm text-primary-500 hover:text-primary-400 transition-colors"
                      >
                        {showQuitSims ? 'Hide' : `Show (${quitSimulations.length})`}
                      </button>
                    </div>

                    {showQuitSims && (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {quitSimulations.map((sim) => (
                          <div key={sim.id} className="card group opacity-75">
                            <div className="flex items-start justify-between mb-4">
                              <div>
                                <h3 className="text-lg font-semibold text-dark-text mb-1">
                                  {sim.name || `Season ${sim.current_season} / ${sim.year_length}`}
                                </h3>
                                <p className="text-sm text-dark-text-muted">
                                  {sim.name ? `Season ${sim.current_season} / ${sim.year_length}` : ''} {sim.num_teams} Teams • {new Date(sim.created_at!).toLocaleDateString()}
                                </p>
                              </div>
                              <button
                                onClick={() => handleDelete(sim.id)}
                                disabled={deletingId === sim.id}
                                className="opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-red-500/20 rounded-lg text-red-400 disabled:opacity-50"
                                title="Delete simulation"
                              >
                                {deletingId === sim.id ? (
                                  <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin"></div>
                                ) : (
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                )}
                              </button>
                            </div>

                            <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border mb-4 ${getStatusColor(sim.status)}`}>
                              {sim.status.charAt(0).toUpperCase() + sim.status.slice(1)}
                            </div>

                            <div className="flex items-center gap-4 text-sm text-dark-text-muted mb-4">
                              <span>Date: {sim.current_date}</span>
                            </div>

                            <button
                              onClick={() => handleRejoin(sim.id)}
                              className="btn btn-primary w-full"
                            >
                              Rejoin Simulation
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </>
        )}

        {/* Call to Action for non-authenticated users */}
        {!isAuthenticated && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <Link href="/simulation/new" className="card-hover group">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-orange flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-dark-text group-hover:text-primary-500 transition-colors">
                    New Simulation
                  </h3>
                  <p className="text-sm text-dark-text-muted">Start a new season</p>
                </div>
              </div>
            </Link>

            <Link href="/login" className="card-hover group">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-lg bg-primary-500 flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-dark-text group-hover:text-primary-500 transition-colors">
                    Login / Sign Up
                  </h3>
                  <p className="text-sm text-dark-text-muted">Access your account</p>
                </div>
              </div>
            </Link>
          </div>
        )}

        {/* How It Works Card */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-6 text-dark-text">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                  1
                </div>
                <div>
                  <h3 className="font-semibold text-dark-text mb-1">Create Simulation</h3>
                  <p className="text-sm text-dark-text-muted">
                    Choose league size (4-12 teams) and season length (20-25 years)
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                  2
                </div>
                <div>
                  <h3 className="font-semibold text-dark-text mb-1">Draft Your Team</h3>
                  <p className="text-sm text-dark-text-muted">
                    Build your dream team of hockey legends in snake draft format
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                  3
                </div>
                <div>
                  <h3 className="font-semibold text-dark-text mb-1">Configure Strategy</h3>
                  <p className="text-sm text-dark-text-muted">
                    Set your lines and team strategy for optimal performance
                  </p>
                </div>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                  4
                </div>
                <div>
                  <h3 className="font-semibold text-dark-text mb-1">Simulate Seasons</h3>
                  <p className="text-sm text-dark-text-muted">
                    Watch your team compete through regular seasons and playoffs
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                  5
                </div>
                <div>
                  <h3 className="font-semibold text-dark-text mb-1">Track Stats</h3>
                  <p className="text-sm text-dark-text-muted">
                    Monitor player and team statistics across multiple seasons
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                  6
                </div>
                <div>
                  <h3 className="font-semibold text-dark-text mb-1">Build a Dynasty</h3>
                  <p className="text-sm text-dark-text-muted">
                    Compete for championships and build your legacy
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}