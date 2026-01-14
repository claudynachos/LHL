'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

export default function NewSimulationPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    year_length: 20,
    num_teams: 6
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="card max-w-2xl w-full">
        <h1 className="text-4xl font-bold text-center mb-2 text-primary-600">
          Create New Simulation
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Configure your league settings
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-lg font-medium mb-2">
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
            <p className="text-sm text-gray-500 mt-1">
              How many seasons to simulate
            </p>
          </div>

          <div>
            <label className="block text-lg font-medium mb-2">
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
            <p className="text-sm text-gray-500 mt-1">
              League size determines playoff format
            </p>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Game Mode</h3>
            <div className="flex items-center gap-2">
              <input type="radio" checked readOnly />
              <label>Solo (vs AI)</label>
            </div>
            <div className="flex items-center gap-2 opacity-50">
              <input type="radio" disabled />
              <label>Multiplayer (Coming in V2)</label>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full text-xl py-3"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Start Draft →'}
          </button>
        </form>
      </div>
    </div>
  );
}
