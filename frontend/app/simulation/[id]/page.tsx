'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { Simulation, Standing } from '@/lib/types';
import DashboardLayout from '@/app/components/DashboardLayout';

export default function SimulationPage() {
  const params = useParams();
  const simulationId = params.id;
  const router = useRouter();

  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simulationProgress, setSimulationProgress] = useState<{
    games_simulated: number;
    total_games: number;
    percentage: number;
  } | null>(null);
  
  // Season complete animation state
  const [showSeasonComplete, setShowSeasonComplete] = useState(false);
  const [cupWinnerName, setCupWinnerName] = useState('');
  const [animationTimer, setAnimationTimer] = useState(10);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const animationTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Check for season complete flag on mount
  useEffect(() => {
    loadSimulation();
    
    // Check if coming from playoffs completion
    const seasonComplete = sessionStorage.getItem('seasonComplete');
    const cupWinner = sessionStorage.getItem('cupWinner');
    
    if (seasonComplete === 'true') {
      // Clear the flags immediately
      sessionStorage.removeItem('seasonComplete');
      sessionStorage.removeItem('cupWinner');
      
      // Trigger the animation
      setCupWinnerName(cupWinner || '');
      setAnimationTimer(10);
      setShowSeasonComplete(true);
    }
  }, []);
  
  // Handle countdown timer when animation is shown
  useEffect(() => {
    if (!showSeasonComplete) return;
    
    // Play audio
    const audio = new Audio('/HockeyNightinCanada.mp3');
    audio.volume = 1;
    audio.play().catch(error => {
      console.error('Failed to play audio:', error);
    });
    audioRef.current = audio;
    
    // Start countdown
    let countdown = 10;
    const timerId = setInterval(() => {
      countdown -= 1;
      setAnimationTimer(countdown);
      if (countdown <= 0) {
        clearInterval(timerId);
        setShowSeasonComplete(false);
      }
    }, 1000);
    animationTimerRef.current = timerId;
    
    // Cleanup
    return () => {
      if (animationTimerRef.current) {
        clearInterval(animationTimerRef.current);
        animationTimerRef.current = null;
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [showSeasonComplete]);
  
  const dismissSeasonComplete = () => {
    if (animationTimerRef.current) {
      clearInterval(animationTimerRef.current);
      animationTimerRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setShowSeasonComplete(false);
  };

  const loadSimulation = async () => {
    try {
      const response = await api.get(`/api/simulations/${simulationId}`);
      setSimulation(response.data.simulation);

      const standingsResponse = await api.get(`/api/stats/standings/${simulationId}`);
      const allStandings = [...standingsResponse.data.eastern, ...standingsResponse.data.western];
      setStandings(allStandings);
    } catch (error) {
      console.error('Failed to load simulation', error);
    } finally {
      setLoading(false);
    }
  };

  const simulateToPlayoffs = async () => {
    setSimulating(true);
    
    // Get initial progress to show total games
    try {
      const initialProgress = await api.get(`/api/simulations/${simulationId}/simulation-progress`);
      setSimulationProgress(initialProgress.data);
    } catch (error) {
      console.error('Failed to get initial progress', error);
      setSimulationProgress({ games_simulated: 0, total_games: 0, percentage: 0 });
    }
    
    // Start polling for progress
    const progressInterval = setInterval(async () => {
      try {
        const progressResponse = await api.get(`/api/simulations/${simulationId}/simulation-progress`);
        setSimulationProgress(progressResponse.data);
      } catch (error) {
        console.error('Failed to get progress', error);
      }
    }, 300); // Poll every 300ms for smoother updates
    
    try {
      await api.post(`/api/simulations/${simulationId}/simulate-to-playoffs`);
      clearInterval(progressInterval);
      // Get final progress
      const finalProgress = await api.get(`/api/simulations/${simulationId}/simulation-progress`);
      setSimulationProgress(finalProgress.data);
      await loadSimulation();
    } catch (error) {
      console.error('Simulation failed', error);
      clearInterval(progressInterval);
    } finally {
      setSimulating(false);
      setSimulationProgress(null);
    }
  };

  const simulateSeason = async () => {
    setSimulating(true);
    
    // Get initial progress to show total games
    try {
      const initialProgress = await api.get(`/api/simulations/${simulationId}/simulation-progress`);
      setSimulationProgress(initialProgress.data);
    } catch (error) {
      console.error('Failed to get initial progress', error);
      setSimulationProgress({ games_simulated: 0, total_games: 0, percentage: 0 });
    }
    
    // Start polling for progress
    const progressInterval = setInterval(async () => {
      try {
        const progressResponse = await api.get(`/api/simulations/${simulationId}/simulation-progress`);
        setSimulationProgress(progressResponse.data);
      } catch (error) {
        console.error('Failed to get progress', error);
      }
    }, 300); // Poll every 300ms for smoother updates
    
    try {
      await api.post(`/api/simulations/${simulationId}/simulate-season`);
      clearInterval(progressInterval);
      // Get final progress
      const finalProgress = await api.get(`/api/simulations/${simulationId}/simulation-progress`);
      setSimulationProgress(finalProgress.data);
      await loadSimulation();
    } catch (error) {
      console.error('Simulation failed', error);
      clearInterval(progressInterval);
    } finally {
      setSimulating(false);
      setSimulationProgress(null);
    }
  };

  const enterPlayoffs = async () => {
    setSimulating(true);
    try {
      await api.post(`/api/simulations/${simulationId}/enter-playoffs`);
      router.push(`/simulation/${simulationId}/playoffs`);
    } catch (error) {
      console.error('Enter playoffs failed', error);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-dark-text-muted">Loading simulation...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Season Complete Animation */}
      {showSeasonComplete && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center">
          <div className="text-center animate-fade-in max-w-lg mx-4">
            <div className="text-6xl mb-6">🏒</div>
            <h1 className="text-4xl font-bold text-primary-500 mb-4">
              SEASON COMPLETE
            </h1>
            {cupWinnerName && (
              <p className="text-xl text-white mb-4">
                {cupWinnerName} are your Stanley Cup Champions!
              </p>
            )}
            <p className="text-lg text-dark-text-muted mb-6">
              A new season is about to begin.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <Link
                href={`/simulation/${simulationId}/hall-of-fame?tab=trophies`}
                onClick={dismissSeasonComplete}
                className="btn btn-primary px-6 py-3"
              >
                View Trophy Winners
              </Link>
              <button
                onClick={dismissSeasonComplete}
                className="btn btn-secondary px-6 py-3"
              >
                Continue ({animationTimer}s)
              </button>
            </div>
          </div>
        </div>
      )}
      
      <div className="max-w-7xl mx-auto">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-dark-text mb-2">
            {simulation?.name || `Season ${simulation?.current_season}`}
          </h1>
          <div className="flex items-center gap-4 text-dark-text-muted">
            {simulation?.name && (
              <>
                <span>Season {simulation?.current_season} / {simulation?.year_length}</span>
                <span>•</span>
              </>
            )}
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary-500"></span>
              Status: <span className="text-dark-text font-semibold capitalize">{simulation?.status}</span>
            </span>
            <span>•</span>
            <span>Date: {simulation?.current_date}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Simulation Actions Card */}
            <div className="card">
              <h2 className="text-2xl font-bold mb-6 text-dark-text">Simulation Actions</h2>
              <div className="space-y-4">
                <button
                  onClick={simulateToPlayoffs}
                  disabled={simulating || simulation?.status !== 'season'}
                  className="btn btn-primary w-full text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {simulating ? 'Simulating...' : 'Simulate to Playoffs'}
                </button>

                {simulation?.status === 'season_end' && (
                  <button
                    onClick={enterPlayoffs}
                    disabled={simulating}
                    className="btn btn-primary w-full text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Enter Playoffs
                  </button>
                )}

                <button
                  onClick={simulateSeason}
                  disabled={simulating || simulation?.status !== 'season'}
                  className="btn btn-primary w-full text-lg py-4 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {simulating ? 'Simulating...' : 'Simulate Full Season'}
                </button>
              </div>

              {simulating && simulationProgress && (
                <div className="mt-6 bg-primary-500/10 border border-primary-500/20 p-4 rounded-lg">
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="text-primary-400 font-medium">Simulating games...</span>
                    {simulationProgress.total_games > 0 ? (
                      <span className="text-primary-400">
                        {simulationProgress.games_simulated} / {simulationProgress.total_games} games
                      </span>
                    ) : (
                      <span className="text-primary-400">Preparing schedule...</span>
                    )}
                  </div>
                  {simulationProgress.total_games > 0 ? (
                    <>
                      <div className="w-full bg-dark-surface rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-primary-500 h-full transition-all duration-300 ease-out"
                          style={{ width: `${Math.min(simulationProgress.percentage, 100)}%` }}
                        ></div>
                      </div>
                      <p className="text-center text-primary-400 text-xs mt-2">
                        {simulationProgress.percentage.toFixed(1)}% complete
                      </p>
                    </>
                  ) : (
                    <div className="w-full bg-dark-surface rounded-full h-3 overflow-hidden">
                      <div className="bg-primary-500 h-full animate-pulse" style={{ width: '30%' }}></div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Quick Navigation */}
            <div className="card">
              <h2 className="text-xl font-bold mb-4 text-dark-text">Quick Navigation</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <Link 
                  href={`/simulation/${simulationId}/stats`}
                  className="card-hover text-center p-4 group"
                >
                  <div className="text-2xl mb-2">📊</div>
                  <div className="text-sm font-medium text-dark-text group-hover:text-primary-500 transition-colors">
                    Season Stats
                  </div>
                </Link>
                <Link 
                  href={`/simulation/${simulationId}/standings`}
                  className="card-hover text-center p-4 group"
                >
                  <div className="text-2xl mb-2">🏆</div>
                  <div className="text-sm font-medium text-dark-text group-hover:text-primary-500 transition-colors">
                    Standings
                  </div>
                </Link>
                <Link 
                  href={`/simulation/${simulationId}/lines`}
                  className="card-hover text-center p-4 group"
                >
                  <div className="text-2xl mb-2">⚙️</div>
                  <div className="text-sm font-medium text-dark-text group-hover:text-primary-500 transition-colors">
                    Lines Config
                  </div>
                </Link>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Current Standings */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-dark-text">Current Standings</h3>
                <Link 
                  href={`/simulation/${simulationId}/standings`} 
                  className="text-sm text-primary-500 hover:text-primary-400 transition-colors"
                >
                  View all →
                </Link>
              </div>
              <div className="space-y-3">
                {standings.slice(0, 5).map((s: any, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-primary-500/20 flex items-center justify-center text-xs font-bold text-primary-400">
                        {idx + 1}
                      </div>
                      <span className="text-sm text-dark-text font-medium">{s.team_name}</span>
                    </div>
                    <span className="text-sm font-mono text-dark-text-muted">{s.wins}-{s.losses}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-dark-text">Quick Stats</h3>
                <Link 
                  href={`/simulation/${simulationId}/stats`} 
                  className="text-sm text-primary-500 hover:text-primary-400 transition-colors"
                >
                  View all →
                </Link>
              </div>
              <p className="text-sm text-dark-text-muted">Season Leaders</p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
