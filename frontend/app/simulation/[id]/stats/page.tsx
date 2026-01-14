'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import { PlayerStats } from '@/lib/types';

export default function StatsPage() {
  const params = useParams();
  const simulationId = params.id;

  const [stats, setStats] = useState<PlayerStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('points');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await api.get(`/api/stats/season/${simulationId}`);
      setStats(response.data.stats);
    } catch (error) {
      console.error('Failed to load stats', error);
    } finally {
      setLoading(false);
    }
  };

  const sortedStats = [...stats].sort((a, b) => {
    return (b as any)[sortBy] - (a as any)[sortBy];
  });

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading stats...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="card mb-4">
          <h1 className="text-3xl font-bold">Season Stats Leaders</h1>
        </div>

        <div className="card">
          <div className="flex gap-4 mb-4">
            <select
              className="input"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="points">Points</option>
              <option value="goals">Goals</option>
              <option value="assists">Assists</option>
              <option value="plus_minus">Plus/Minus</option>
              <option value="hits">Hits</option>
              <option value="blocks">Blocks</option>
            </select>
          </div>

          <div className="overflow-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="p-3 text-left">Rank</th>
                  <th className="p-3 text-left">Player</th>
                  <th className="p-3 text-left">Team</th>
                  <th className="p-3 text-center">GP</th>
                  <th className="p-3 text-center">G</th>
                  <th className="p-3 text-center">A</th>
                  <th className="p-3 text-center">PTS</th>
                  <th className="p-3 text-center">+/-</th>
                  <th className="p-3 text-center">Hits</th>
                  <th className="p-3 text-center">Blocks</th>
                </tr>
              </thead>
              <tbody>
                {sortedStats.map((stat, idx) => (
                  <tr key={stat.player_id} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-bold">{idx + 1}</td>
                    <td className="p-3 font-medium">{stat.player_name}</td>
                    <td className="p-3">{stat.team_name}</td>
                    <td className="p-3 text-center">{stat.games_played}</td>
                    <td className="p-3 text-center">{stat.goals}</td>
                    <td className="p-3 text-center">{stat.assists}</td>
                    <td className="p-3 text-center font-bold">{stat.points}</td>
                    <td className={`p-3 text-center ${stat.plus_minus >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {stat.plus_minus >= 0 ? '+' : ''}{stat.plus_minus}
                    </td>
                    <td className="p-3 text-center">{stat.hits}</td>
                    <td className="p-3 text-center">{stat.blocks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
