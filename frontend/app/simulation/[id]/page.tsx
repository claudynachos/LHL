'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { Simulation, Standing } from '@/lib/types';

export default function SimulationPage() {
  const params = useParams();
  const simulationId = params.id;

  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    loadSimulation();
  }, []);

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
    try {
      await api.post(`/api/simulations/${simulationId}/simulate-to-playoffs`);
      await loadSimulation();
    } catch (error) {
      console.error('Simulation failed', error);
    } finally {
      setSimulating(false);
    }
  };

  const simulateSeason = async () => {
    setSimulating(true);
    try {
      await api.post(`/api/simulations/${simulationId}/simulate-season`);
      await loadSimulation();
    } catch (error) {
      console.error('Simulation failed', error);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading simulation...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="grid grid-cols-12 gap-4 p-4">
        {/* Left Sidebar */}
        <div className="col-span-2 space-y-2">
          <div className="card">
            <h3 className="font-bold mb-2">Menu</h3>
            <nav className="space-y-1">
              <Link href={`/simulation/${simulationId}/calendar`} className="block p-2 hover:bg-gray-100 rounded">
                Calendar
              </Link>
              <Link href={`/simulation/${simulationId}/stats`} className="block p-2 hover:bg-gray-100 rounded">
                Season Stats
              </Link>
              <Link href={`/simulation/${simulationId}/stats/alltime`} className="block p-2 hover:bg-gray-100 rounded">
                All-Time Stats
              </Link>
              <Link href={`/simulation/${simulationId}/trophies`} className="block p-2 hover:bg-gray-100 rounded">
                Trophies
              </Link>
              <Link href={`/simulation/${simulationId}/lines`} className="block p-2 hover:bg-gray-100 rounded">
                Lines Config
              </Link>
              <Link href={`/simulation/${simulationId}/standings`} className="block p-2 hover:bg-gray-100 rounded">
                Standings
              </Link>
            </nav>
          </div>
        </div>

        {/* Center Panel */}
        <div className="col-span-7">
          <div className="card mb-4">
            <h1 className="text-3xl font-bold mb-2">
              Season {simulation?.current_season}
            </h1>
            <p className="text-gray-600">
              Status: <span className="font-semibold capitalize">{simulation?.status}</span>
            </p>
            <p className="text-gray-600">
              Date: {simulation?.current_date}
            </p>
          </div>

          <div className="card">
            <h2 className="text-2xl font-bold mb-4">Simulation Actions</h2>
            <div className="space-y-3">
              <button
                onClick={simulateToPlayoffs}
                disabled={simulating || simulation?.status === 'playoffs'}
                className="btn btn-primary w-full text-lg py-3"
              >
                {simulating ? 'Simulating...' : 'Simulate to Playoffs'}
              </button>

              <button
                onClick={() => {/* Simulate Round */}}
                disabled={simulating || simulation?.status !== 'playoffs'}
                className="btn btn-primary w-full text-lg py-3"
              >
                Simulate Playoff Round
              </button>

              <button
                onClick={simulateSeason}
                disabled={simulating}
                className="btn btn-primary w-full text-lg py-3"
              >
                {simulating ? 'Simulating...' : 'Simulate Full Season'}
              </button>
            </div>

            {simulating && (
              <div className="mt-4 bg-blue-50 p-4 rounded-lg">
                <p className="text-center">Simulating games... This may take a moment.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Info Panel */}
        <div className="col-span-3">
          <div className="card">
            <h3 className="font-bold mb-3">Current Standings</h3>
            <div className="space-y-2">
              {standings.slice(0, 5).map((s: any, idx) => (
                <div key={idx} className="flex justify-between text-sm">
                  <span>{s.team_name}</span>
                  <span className="font-mono">{s.wins}-{s.losses}</span>
                </div>
              ))}
            </div>
            <Link href={`/simulation/${simulationId}/standings`} className="text-primary-600 text-sm mt-2 block">
              View Full Standings →
            </Link>
          </div>

          <div className="card mt-4">
            <h3 className="font-bold mb-2">Quick Stats</h3>
            <p className="text-sm text-gray-600">Season Leaders</p>
            <Link href={`/simulation/${simulationId}/stats`} className="text-primary-600 text-sm mt-2 block">
              View All Stats →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
