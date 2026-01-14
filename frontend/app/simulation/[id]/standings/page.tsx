'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';

export default function StandingsPage() {
  const params = useParams();
  const simulationId = params.id;

  const [eastern, setEastern] = useState<any[]>([]);
  const [western, setWestern] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStandings();
  }, []);

  const loadStandings = async () => {
    try {
      const response = await api.get(`/api/stats/standings/${simulationId}`);
      setEastern(response.data.eastern);
      setWestern(response.data.western);
    } catch (error) {
      console.error('Failed to load standings', error);
    } finally {
      setLoading(false);
    }
  };

  const renderConference = (name: string, standings: any[]) => (
    <div className="card">
      <h2 className="text-2xl font-bold mb-4">{name} Conference</h2>
      <table className="w-full">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-3 text-left">Team</th>
            <th className="p-3 text-center">W</th>
            <th className="p-3 text-center">L</th>
            <th className="p-3 text-center">PTS</th>
            <th className="p-3 text-center">GF</th>
            <th className="p-3 text-center">GA</th>
            <th className="p-3 text-center">DIFF</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((team, idx) => (
            <tr key={idx} className="border-b hover:bg-gray-50">
              <td className="p-3 font-medium">{team.team_name}</td>
              <td className="p-3 text-center">{team.wins}</td>
              <td className="p-3 text-center">{team.losses}</td>
              <td className="p-3 text-center font-bold">{team.points}</td>
              <td className="p-3 text-center">{team.goals_for}</td>
              <td className="p-3 text-center">{team.goals_against}</td>
              <td className={`p-3 text-center ${(team.goals_for - team.goals_against) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {team.goals_for - team.goals_against >= 0 ? '+' : ''}{team.goals_for - team.goals_against}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading standings...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="card">
          <h1 className="text-3xl font-bold">League Standings</h1>
        </div>

        {renderConference('Eastern', eastern)}
        {renderConference('Western', western)}
      </div>
    </div>
  );
}
