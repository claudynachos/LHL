'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { Player, Team } from '@/lib/types';

export default function DraftPage() {
  const router = useRouter();
  const params = useParams();
  const simulationId = params.id;

  const [availablePlayers, setAvailablePlayers] = useState<Player[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [currentPick, setCurrentPick] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('off');

  useEffect(() => {
    loadDraftData();
  }, []);

  const loadDraftData = async () => {
    try {
      // Load simulation and teams
      const simResponse = await api.get(`/api/simulations/${simulationId}`);
      setTeams(simResponse.data.teams);

      // Load all players
      const playersResponse = await api.get('/api/players');
      setAvailablePlayers(playersResponse.data.players || []);

      // Get current pick info
      const pickResponse = await api.get(`/api/simulations/${simulationId}/draft/current`);
      setCurrentPick(pickResponse.data);
    } catch (error) {
      console.error('Failed to load draft data', error);
    } finally {
      setLoading(false);
    }
  };

  const makePick = async (playerId: number) => {
    try {
      const response = await api.post(`/api/simulations/${simulationId}/draft`, {
        player_id: playerId
      });

      if (response.data.draft_complete) {
        router.push(`/simulation/${simulationId}`);
      } else {
        setCurrentPick(response.data.next_pick);
        // Remove picked player
        setAvailablePlayers(availablePlayers.filter(p => p.id !== playerId));
      }
    } catch (error) {
      console.error('Failed to make pick', error);
    }
  };

  const filteredPlayers = availablePlayers
    .filter(p => filter === 'all' || p.position === filter)
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      return (b as any)[sortBy] - (a as any)[sortBy];
    });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading draft...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="card mb-4">
          <h1 className="text-3xl font-bold mb-2">Draft</h1>
          {currentPick && (
            <div className="bg-primary-50 p-4 rounded-lg">
              <p className="text-lg">
                <span className="font-bold">Round {currentPick.round}</span> - Pick {currentPick.pick}/{currentPick.total_picks}
              </p>
              <p className="text-xl font-bold text-primary-600">
                {currentPick.team_name} is picking...
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-4 gap-4">
          {/* Available Players */}
          <div className="col-span-3 card">
            <div className="flex gap-4 mb-4">
              <select
                className="input"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="all">All Positions</option>
                <option value="C">Centers</option>
                <option value="LW">Left Wing</option>
                <option value="RW">Right Wing</option>
                <option value="D">Defense</option>
                <option value="G">Goalies</option>
              </select>

              <select
                className="input"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="off">Offense</option>
                <option value="def">Defense</option>
                <option value="phys">Physical</option>
                <option value="name">Name</option>
              </select>
            </div>

            <div className="overflow-auto max-h-96">
              <table className="w-full">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="p-2 text-left">Player</th>
                    <th className="p-2">Pos</th>
                    <th className="p-2">OFF</th>
                    <th className="p-2">DEF</th>
                    <th className="p-2">PHYS</th>
                    <th className="p-2">LEAD</th>
                    <th className="p-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPlayers.map(player => (
                    <tr key={player.id} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-medium">{player.name}</td>
                      <td className="p-2 text-center">{player.position}</td>
                      <td className="p-2 text-center">{player.off}</td>
                      <td className="p-2 text-center">{player.def}</td>
                      <td className="p-2 text-center">{player.phys}</td>
                      <td className="p-2 text-center">{player.lead}</td>
                      <td className="p-2">
                        {currentPick?.is_user_team && (
                          <button
                            onClick={() => makePick(player.id)}
                            className="btn btn-primary btn-sm"
                          >
                            Draft
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Draft Board */}
          <div className="card">
            <h3 className="font-bold mb-2">Teams</h3>
            <div className="space-y-2">
              {teams.map(team => (
                <div key={team.id} className={`p-2 rounded ${team.user_controlled ? 'bg-primary-100 font-bold' : 'bg-gray-100'}`}>
                  {team.city} {team.name}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
