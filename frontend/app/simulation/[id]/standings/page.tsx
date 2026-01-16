'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import DashboardLayout from '@/app/components/DashboardLayout';

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

  const calculatePlayoffCutoff = (totalTeams: number): number => {
    // Calculate teams per conference that make playoffs
    // 4 teams: all 4 make playoffs → 2 per conference
    // 6 teams: top 4 make playoffs → 2 per conference
    // 8 teams: all 8 make playoffs → 4 per conference
    // 10 teams: top 8 make playoffs → 4 per conference
    // 12 teams: top 8 make playoffs → 4 per conference
    if (totalTeams === 4 || totalTeams === 6) {
      return 2;
    } else if (totalTeams === 8 || totalTeams === 10 || totalTeams === 12) {
      return 4;
    }
    // Fallback: split evenly
    const playoffTeams = totalTeams <= 6 ? 4 : 8;
    return playoffTeams / 2;
  };

  const renderConference = (name: string, standings: any[]) => {
    const totalTeams = eastern.length + western.length;
    const playoffCutoff = calculatePlayoffCutoff(totalTeams);
    
    return (
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 text-dark-text">{name} Conference</h2>
        <div className="overflow-auto">
          <table className="w-full">
            <thead className="bg-dark-surface">
              <tr>
                <th className="p-3 text-left text-dark-text">Team</th>
                <th className="p-3 text-center text-dark-text">W</th>
                <th className="p-3 text-center text-dark-text">L</th>
                <th className="p-3 text-center text-dark-text">OTL</th>
                <th className="p-3 text-center text-dark-text">PTS</th>
                <th className="p-3 text-center text-dark-text">GF</th>
                <th className="p-3 text-center text-dark-text">GA</th>
                <th className="p-3 text-center text-dark-text">DIFF</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((team, idx) => (
                <tr 
                  key={idx} 
                  className={`hover:bg-dark-surface ${
                    idx === playoffCutoff - 1 
                      ? 'border-b-2 border-orange-500' 
                      : 'border-b border-dark-border'
                  }`}
                >
                  <td className="p-3 font-medium text-dark-text">{team.team_name}</td>
                  <td className="p-3 text-center text-dark-text">{team.wins}</td>
                  <td className="p-3 text-center text-dark-text">{team.losses}</td>
                  <td className="p-3 text-center text-dark-text">{team.ot_losses || 0}</td>
                  <td className="p-3 text-center font-bold text-dark-text">{team.points}</td>
                  <td className="p-3 text-center text-dark-text">{team.goals_for}</td>
                  <td className="p-3 text-center text-dark-text">{team.goals_against}</td>
                  <td className={`p-3 text-center ${(team.goals_for - team.goals_against) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {team.goals_for - team.goals_against >= 0 ? '+' : ''}{team.goals_for - team.goals_against}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-dark-text-muted">Loading standings...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-dark-text">League Standings</h1>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {renderConference('Eastern', eastern)}
          {renderConference('Western', western)}
        </div>
      </div>
    </DashboardLayout>
  );
}
