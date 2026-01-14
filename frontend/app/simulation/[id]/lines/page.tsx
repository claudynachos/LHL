'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';

export default function LinesPage() {
  const params = useParams();
  const simulationId = params.id;

  const [teams, setTeams] = useState<any[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [roster, setRoster] = useState<any[]>([]);
  const [lines, setLines] = useState<any>({
    forwards: [[], [], [], []],
    defense: [[], [], []],
    goalies: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTeams();
  }, []);

  useEffect(() => {
    if (selectedTeam) {
      loadTeamData(selectedTeam);
    }
  }, [selectedTeam]);

  const loadTeams = async () => {
    try {
      const response = await api.get(`/api/simulations/${simulationId}`);
      setTeams(response.data.teams);
      if (response.data.teams.length > 0) {
        setSelectedTeam(response.data.teams[0].id.toString());
      }
    } catch (error) {
      console.error('Failed to load teams', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTeamData = async (teamId: string) => {
    try {
      const response = await api.get(`/api/teams/${teamId}`);
      setRoster(response.data.roster);
      // Parse lines data here
    } catch (error) {
      console.error('Failed to load team data', error);
    }
  };

  const saveLines = async () => {
    // Convert lines state to API format and save
    try {
      await api.put(`/api/teams/${selectedTeam}/lines`, { lines: [] });
      alert('Lines saved successfully!');
    } catch (error) {
      console.error('Failed to save lines', error);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="card mb-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold">Lines Configuration</h1>
            <select
              className="input"
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
            >
              {teams.map(team => (
                <option key={team.id} value={team.id}>
                  {team.city} {team.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold mb-4">Forward Lines</h2>
          {[1, 2, 3, 4].map(lineNum => (
            <div key={lineNum} className="mb-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-bold mb-2">Line {lineNum}</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Left Wing</label>
                  <select className="input">
                    <option>Select Player</option>
                    {roster.filter(p => p.position === 'LW').map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Center</label>
                  <select className="input">
                    <option>Select Player</option>
                    {roster.filter(p => p.position === 'C').map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Right Wing</label>
                  <select className="input">
                    <option>Select Player</option>
                    {roster.filter(p => p.position === 'RW').map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          ))}

          <h2 className="text-2xl font-bold mb-4 mt-6">Defense Pairs</h2>
          {[1, 2, 3].map(pairNum => (
            <div key={pairNum} className="mb-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-bold mb-2">Pair {pairNum}</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Left Defense</label>
                  <select className="input">
                    <option>Select Player</option>
                    {roster.filter(p => p.position === 'D').map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Right Defense</label>
                  <select className="input">
                    <option>Select Player</option>
                    {roster.filter(p => p.position === 'D').map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          ))}

          <h2 className="text-2xl font-bold mb-4 mt-6">Goalies</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-bold">Starter (G1)</label>
              <select className="input">
                <option>Select Goalie</option>
                {roster.filter(p => p.position === 'G').map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-bold">Backup (G2)</label>
              <select className="input">
                <option>Select Goalie</option>
                {roster.filter(p => p.position === 'G').map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={saveLines}
            className="btn btn-primary w-full mt-6 text-lg py-3"
          >
            Save Lines
          </button>
        </div>
      </div>
    </div>
  );
}
