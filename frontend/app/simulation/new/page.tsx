'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import DashboardLayout from '@/app/components/DashboardLayout';
import { useAuth } from '@/lib/auth';

// Team configurations - matches backend exactly
// East Conference: MTL, BOS, TOR (6+), PHI (8+), PIT (10+), QC (12+)
// West Conference: DET, CHI, NYR (6+), LA (8+), EDM (10+), NYI (12+)
const TEAM_CONFIGS: { [key: number]: Array<{ name: string; city: string; conference: string }> } = {
  4: [
    { name: 'MTL', city: 'Montreal', conference: 'Eastern' },
    { name: 'BOS', city: 'Boston', conference: 'Eastern' },
    { name: 'DET', city: 'Detroit', conference: 'Western' },
    { name: 'CHI', city: 'Chicago', conference: 'Western' },
  ],
  6: [
    { name: 'MTL', city: 'Montreal', conference: 'Eastern' },
    { name: 'BOS', city: 'Boston', conference: 'Eastern' },
    { name: 'TOR', city: 'Toronto', conference: 'Eastern' },
    { name: 'DET', city: 'Detroit', conference: 'Western' },
    { name: 'CHI', city: 'Chicago', conference: 'Western' },
    { name: 'NYR', city: 'New York', conference: 'Western' },
  ],
  8: [
    { name: 'MTL', city: 'Montreal', conference: 'Eastern' },
    { name: 'BOS', city: 'Boston', conference: 'Eastern' },
    { name: 'TOR', city: 'Toronto', conference: 'Eastern' },
    { name: 'PHI', city: 'Philadelphia', conference: 'Eastern' },
    { name: 'DET', city: 'Detroit', conference: 'Western' },
    { name: 'CHI', city: 'Chicago', conference: 'Western' },
    { name: 'NYR', city: 'New York', conference: 'Western' },
    { name: 'LA', city: 'Los Angeles', conference: 'Western' },
  ],
  10: [
    { name: 'MTL', city: 'Montreal', conference: 'Eastern' },
    { name: 'BOS', city: 'Boston', conference: 'Eastern' },
    { name: 'TOR', city: 'Toronto', conference: 'Eastern' },
    { name: 'PHI', city: 'Philadelphia', conference: 'Eastern' },
    { name: 'PIT', city: 'Pittsburgh', conference: 'Eastern' },
    { name: 'DET', city: 'Detroit', conference: 'Western' },
    { name: 'CHI', city: 'Chicago', conference: 'Western' },
    { name: 'NYR', city: 'New York', conference: 'Western' },
    { name: 'LA', city: 'Los Angeles', conference: 'Western' },
    { name: 'EDM', city: 'Edmonton', conference: 'Western' },
  ],
  12: [
    { name: 'MTL', city: 'Montreal', conference: 'Eastern' },
    { name: 'BOS', city: 'Boston', conference: 'Eastern' },
    { name: 'TOR', city: 'Toronto', conference: 'Eastern' },
    { name: 'PHI', city: 'Philadelphia', conference: 'Eastern' },
    { name: 'PIT', city: 'Pittsburgh', conference: 'Eastern' },
    { name: 'QC', city: 'Quebec', conference: 'Eastern' },
    { name: 'DET', city: 'Detroit', conference: 'Western' },
    { name: 'CHI', city: 'Chicago', conference: 'Western' },
    { name: 'NYR', city: 'New York', conference: 'Western' },
    { name: 'LA', city: 'Los Angeles', conference: 'Western' },
    { name: 'EDM', city: 'Edmonton', conference: 'Western' },
    { name: 'NYI', city: 'New York Islanders', conference: 'Western' },
  ],
};

export default function NewSimulationPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    year_length: 20,
    num_teams: 6,
    user_team_index: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Reset team selection when num_teams changes
  useEffect(() => {
    setFormData(prev => ({ ...prev, user_team_index: 0 }));
  }, [formData.num_teams]);

  if (authLoading || !isAuthenticated) {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/simulations/create', formData);
      const simulationId = response.data.simulation.id;
      router.push(`/simulation/${simulationId}/draft`);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create simulation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 text-dark-text">
            Create New Simulation
          </h1>
          <p className="text-dark-text-muted text-lg">
            Configure your league settings and start your journey
          </p>
        </div>

        <div className="card">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-lg font-medium mb-3 text-dark-text">
                Simulation Name (Optional)
              </label>
              <input
                type="text"
                className="input text-lg"
                placeholder="My Awesome Season"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                maxLength={100}
              />
              <p className="text-sm text-dark-text-muted mt-2">
                Give your simulation a memorable name to easily identify it later
              </p>
            </div>

            <div>
              <label className="block text-lg font-medium mb-3 text-dark-text">
                Simulation Length (Years)
              </label>
              <select
                className="input text-lg"
                value={formData.year_length}
                onChange={(e) => setFormData({ ...formData, year_length: parseInt(e.target.value) })}
              >
                {[20, 21, 22, 23, 24, 25].map(years => (
                  <option key={years} value={years}>{years} Years</option>
                ))}
              </select>
              <p className="text-sm text-dark-text-muted mt-2">
                How many seasons to simulate
              </p>
            </div>

            <div>
              <label className="block text-lg font-medium mb-3 text-dark-text">
                Number of Teams
              </label>
              <select
                className="input text-lg"
                value={formData.num_teams}
                onChange={(e) => setFormData({ ...formData, num_teams: parseInt(e.target.value) })}
              >
                {[4, 6, 8, 10, 12].map(teams => (
                  <option key={teams} value={teams}>{teams} Teams</option>
                ))}
              </select>
              <p className="text-sm text-dark-text-muted mt-2">
                League size determines playoff format
              </p>
            </div>

            <div>
              <label className="block text-lg font-medium mb-3 text-dark-text">
                Select Your Team
              </label>
              <div className="space-y-4">
                {/* Eastern Conference */}
                <div>
                  <h4 className="text-sm font-semibold text-dark-text-muted mb-2">Eastern Conference</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {TEAM_CONFIGS[formData.num_teams]
                      .filter(team => team.conference === 'Eastern')
                      .map((team, idx) => {
                        const globalIndex = TEAM_CONFIGS[formData.num_teams].findIndex(t => t.name === team.name);
                        return (
                          <button
                            key={team.name}
                            type="button"
                            onClick={() => setFormData({ ...formData, user_team_index: globalIndex })}
                            className={`p-4 rounded-lg border-2 text-left transition-colors ${
                              formData.user_team_index === globalIndex
                                ? 'border-primary-500 bg-primary-500/10 font-bold text-primary-400'
                                : 'border-dark-border bg-dark-surface hover:border-primary-500/50 text-dark-text'
                            }`}
                          >
                            <div className="font-semibold">{team.city} {team.name}</div>
                          </button>
                        );
                      })}
                  </div>
                </div>
                
                {/* Western Conference */}
                <div>
                  <h4 className="text-sm font-semibold text-dark-text-muted mb-2">Western Conference</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {TEAM_CONFIGS[formData.num_teams]
                      .filter(team => team.conference === 'Western')
                      .map((team, idx) => {
                        const globalIndex = TEAM_CONFIGS[formData.num_teams].findIndex(t => t.name === team.name);
                        return (
                          <button
                            key={team.name}
                            type="button"
                            onClick={() => setFormData({ ...formData, user_team_index: globalIndex })}
                            className={`p-4 rounded-lg border-2 text-left transition-colors ${
                              formData.user_team_index === globalIndex
                                ? 'border-primary-500 bg-primary-500/10 font-bold text-primary-400'
                                : 'border-dark-border bg-dark-surface hover:border-primary-500/50 text-dark-text'
                            }`}
                          >
                            <div className="font-semibold">{team.city} {team.name}</div>
                          </button>
                        );
                      })}
                  </div>
                </div>
              </div>
              <p className="text-sm text-dark-text-muted mt-2">
                Choose which team you will control during the draft and season
              </p>
            </div>

            <div className="bg-dark-surface border border-dark-border p-5 rounded-lg">
              <h3 className="font-semibold mb-4 text-dark-text">Game Mode</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <input 
                    type="radio" 
                    checked 
                    readOnly 
                    className="w-4 h-4 text-primary-500 bg-dark-surface border-dark-border focus:ring-primary-500"
                  />
                  <label className="text-dark-text">Solo (vs AI)</label>
                </div>
                <div className="flex items-center gap-3 opacity-50">
                  <input 
                    type="radio" 
                    disabled 
                    className="w-4 h-4 text-primary-500 bg-dark-surface border-dark-border"
                  />
                  <label className="text-dark-text-muted">Multiplayer (Coming in V2)</label>
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary w-full text-xl py-4"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Start Draft →'}
            </button>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}
