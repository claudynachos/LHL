'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import DashboardLayout from '@/app/components/DashboardLayout';
import { useModal } from '@/app/components/ModalContext';

interface LineAssignment {
  id?: number;
  player_id: number | null;
  line_type: 'forward' | 'defense' | 'goalie';
  line_number: number;
  position: 'LW' | 'C' | 'RW' | 'LD' | 'RD' | 'G';
}

interface Player {
  id: number;
  name: string;
  position: string;
  overall?: number;
}

// Helper function to get name color class based on rating (gold for 100+, silver for 95-100)
const getNameColorClass = (rating: number | undefined): string => {
  if (rating === undefined || rating === null) return '';
  if (rating > 100) return 'text-amber-400 drop-shadow-[0_0_3px_rgba(251,191,36,0.6)]'; // Gold with glow
  if (rating >= 95) return 'text-slate-300 drop-shadow-[0_0_3px_rgba(203,213,225,0.5)]'; // Silver with glow
  return ''; // Default - no special styling
};

export default function LinesPage() {
  const params = useParams();
  const simulationId = params.id;
  const { showAlert } = useModal();

  const [teams, setTeams] = useState<any[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [roster, setRoster] = useState<Player[]>([]);
  const [lines, setLines] = useState<LineAssignment[]>([]);
  const [simulationStatus, setSimulationStatus] = useState<string>('');
  const [selectedTeamData, setSelectedTeamData] = useState<any>(null);
  const [teamOverall, setTeamOverall] = useState<number | null>(null);
  const [coach, setCoach] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSimulation();
  }, []);

  useEffect(() => {
    if (selectedTeam) {
      loadTeamData(selectedTeam);
    }
  }, [selectedTeam]);

  const loadSimulation = async () => {
    try {
      const response = await api.get(`/api/simulations/${simulationId}`);
      setSimulationStatus(response.data.simulation.status);
      setTeams(response.data.teams);
      if (response.data.teams.length > 0) {
        // Find user's team (user_controlled === true) and set it as default
        const userTeam = response.data.teams.find((team: any) => team.user_controlled);
        if (userTeam) {
          setSelectedTeam(userTeam.id.toString());
        } else {
          // Fallback to first team if no user team found
          setSelectedTeam(response.data.teams[0].id.toString());
        }
      }
    } catch (error) {
      console.error('Failed to load simulation', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTeamData = async (teamId: string) => {
    try {
      // Load team data (includes roster, team info, lines)
      const rosterResponse = await api.get(`/api/teams/${teamId}`);
      setRoster(rosterResponse.data.roster || []);
      setSelectedTeamData(rosterResponse.data.team);

      // Load coach if team has one
      if (rosterResponse.data.team?.coach_id) {
        try {
          const coachesResponse = await api.get('/api/players/coaches');
          const coachData = coachesResponse.data.coaches.find((c: any) => c.id === rosterResponse.data.team.coach_id);
          setCoach(coachData || null);
        } catch (error) {
          console.error('Failed to load coach', error);
          setCoach(null);
        }
      } else {
        setCoach(null);
      }

      // Get team overall from API (calculated based on lines and ice time)
      setTeamOverall(rosterResponse.data.team?.overall || null);

      // Load existing line assignments
      const linesResponse = await api.get(`/api/teams/${teamId}/lines`);
      const existingLines = linesResponse.data.lines || [];

      // If no lines exist and draft is complete, auto-populate
      if (existingLines.length === 0 && simulationStatus !== 'draft') {
        await autoPopulateLines(teamId);
      } else {
        setLines(existingLines);
      }
    } catch (error) {
      console.error('Failed to load team data', error);
    }
  };

  const autoPopulateLines = async (teamId: string) => {
    try {
      const response = await api.post(`/api/teams/${teamId}/lines`);
      if (response.data.lines) {
        setLines(response.data.lines);
        // Reload team data to get updated overall rating (skip auto-populate check)
        const rosterResponse = await api.get(`/api/teams/${teamId}`);
        setRoster(rosterResponse.data.roster || []);
        setSelectedTeamData(rosterResponse.data.team);
        setTeamOverall(rosterResponse.data.team?.overall || null);
      }
    } catch (error) {
      console.error('Failed to auto-populate lines', error);
    }
  };

  const getPlayerForPosition = (
    lineType: 'forward' | 'defense' | 'goalie',
    lineNumber: number,
    position: 'LW' | 'C' | 'RW' | 'LD' | 'RD' | 'G'
  ): number | null => {
    const assignment = lines.find(
      l => l.line_type === lineType && l.line_number === lineNumber && l.position === position
    );
    return assignment?.player_id || null;
  };

  const getAssignedPlayerIds = (): Set<number> => {
    return new Set(lines.filter(l => l.player_id !== null).map(l => l.player_id!));
  };

  const updateLineAssignment = (
    lineType: 'forward' | 'defense' | 'goalie',
    lineNumber: number,
    position: 'LW' | 'C' | 'RW' | 'LD' | 'RD' | 'G',
    playerId: number | null
  ) => {
    // Update or create line assignment
    setLines(prevLines => {
      // Remove player from any other line assignment if they're being moved
      let filtered = prevLines.filter(
        l => !(l.line_type === lineType && l.line_number === lineNumber && l.position === position)
      );
      
      // If selecting a player, remove them from any other line they might be on
      if (playerId !== null && playerId !== 0) {
        filtered = filtered.filter(l => l.player_id !== playerId);
        
        const newAssignment: LineAssignment = {
          line_type: lineType,
          line_number: lineNumber,
          position: position,
          player_id: playerId
        };
        return [...filtered, newAssignment];
      }
      
      return filtered;
    });
  };

  const saveLines = async () => {
    setSaving(true);
    try {
      // Convert lines to API format
      const linesData = lines
        .filter(l => l.player_id !== null && l.player_id !== 0)
        .map(l => ({
          player_id: l.player_id!,
          line_type: l.line_type,
          line_number: l.line_number,
          position: l.position
        }));

      await api.put(`/api/teams/${selectedTeam}/lines`, { lines: linesData });
      
      // Reload team data to get updated overall rating
      await loadTeamData(selectedTeam);
      
      await showAlert('Lines saved successfully!');
    } catch (error: any) {
      console.error('Failed to save lines', error);
      const errorMsg = error.response?.data?.error || 'Failed to save lines';
      await showAlert(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const getAvailablePlayers = (position: string): Player[] => {
    return roster.filter(p => p.position === position);
  };

  const getSelectedTeamName = (): string => {
    if (!selectedTeamData) return '';
    return `${selectedTeamData.city} ${selectedTeamData.name}`;
  };

  if (loading) {
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
      <div className="max-w-6xl mx-auto">
        <div className="card mb-4">
          <div className="flex justify-between items-center gap-6">
            <div className="flex items-center gap-4 flex-1">
              <h1 className="text-3xl font-bold text-dark-text">Lines Configuration</h1>
              {selectedTeamData && teamOverall !== null && (
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-500/20 to-primary-600/20 border border-primary-500/30 rounded-lg">
                    <span className="text-sm font-medium text-dark-text-muted">Team OVR</span>
                    <span className="text-xl font-bold text-primary-500">
                      {teamOverall}
                    </span>
                  </div>
                  {selectedTeamData.user_controlled && (
                    <span className="px-3 py-1 text-xs font-semibold bg-primary-500/20 text-primary-400 border border-primary-500/30 rounded-full">
                      Your Team
                    </span>
                  )}
                </div>
              )}
            </div>
            <select
              className="input w-48"
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
          <h2 className="text-2xl font-bold mb-4 text-dark-text">Forward Lines</h2>
          {[1, 2, 3, 4].map(lineNum => (
            <div key={lineNum} className="mb-4 p-4 bg-dark-surface rounded-lg border border-dark-border">
              <h3 className="font-bold mb-2 text-dark-text">Line {lineNum}</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-dark-text-muted">Left Wing</label>
                  <select
                    className="input"
                    value={getPlayerForPosition('forward', lineNum, 'LW') || ''}
                    onChange={(e) => updateLineAssignment('forward', lineNum, 'LW', e.target.value ? parseInt(e.target.value) : null)}
                  >
                    <option value="">Select Player</option>
                    {getAvailablePlayers('LW').map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} {p.overall ? `(${p.overall})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-dark-text-muted">Center</label>
                  <select
                    className="input"
                    value={getPlayerForPosition('forward', lineNum, 'C') || ''}
                    onChange={(e) => updateLineAssignment('forward', lineNum, 'C', e.target.value ? parseInt(e.target.value) : null)}
                  >
                    <option value="">Select Player</option>
                    {getAvailablePlayers('C').map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} {p.overall ? `(${p.overall})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-dark-text-muted">Right Wing</label>
                  <select
                    className="input"
                    value={getPlayerForPosition('forward', lineNum, 'RW') || ''}
                    onChange={(e) => updateLineAssignment('forward', lineNum, 'RW', e.target.value ? parseInt(e.target.value) : null)}
                  >
                    <option value="">Select Player</option>
                    {getAvailablePlayers('RW').map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} {p.overall ? `(${p.overall})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          ))}

          <h2 className="text-2xl font-bold mb-4 mt-6 text-dark-text">Defense Pairs</h2>
          {[1, 2, 3].map(pairNum => (
            <div key={pairNum} className="mb-4 p-4 bg-dark-surface rounded-lg border border-dark-border">
              <h3 className="font-bold mb-2 text-dark-text">Pair {pairNum}</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-dark-text-muted">Left Defense</label>
                  <select
                    className="input"
                    value={getPlayerForPosition('defense', pairNum, 'LD') || ''}
                    onChange={(e) => updateLineAssignment('defense', pairNum, 'LD', e.target.value ? parseInt(e.target.value) : null)}
                  >
                    <option value="">Select Player</option>
                    {getAvailablePlayers('LD').map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} {p.overall ? `(${p.overall})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-dark-text-muted">Right Defense</label>
                  <select
                    className="input"
                    value={getPlayerForPosition('defense', pairNum, 'RD') || ''}
                    onChange={(e) => updateLineAssignment('defense', pairNum, 'RD', e.target.value ? parseInt(e.target.value) : null)}
                  >
                    <option value="">Select Player</option>
                    {getAvailablePlayers('RD').map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} {p.overall ? `(${p.overall})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          ))}

          <h2 className="text-2xl font-bold mb-4 mt-6 text-dark-text">Goalies</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-bold text-dark-text">Starter (G1)</label>
              <select
                className="input"
                value={getPlayerForPosition('goalie', 1, 'G') || ''}
                onChange={(e) => updateLineAssignment('goalie', 1, 'G', e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">Select Goalie</option>
                {getAvailablePlayers('G').map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} {p.overall ? `(${p.overall})` : ''}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-bold text-dark-text">Backup (G2)</label>
              <select
                className="input"
                value={getPlayerForPosition('goalie', 2, 'G') || ''}
                onChange={(e) => updateLineAssignment('goalie', 2, 'G', e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">Select Goalie</option>
                {getAvailablePlayers('G').map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} {p.overall ? `(${p.overall})` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <h2 className="text-2xl font-bold mb-4 mt-6 text-dark-text">Coach</h2>
          <div className="mb-4 p-4 bg-dark-surface rounded-lg border border-dark-border">
            {coach ? (
              <div>
                <div className="font-bold mb-2 text-dark-text">Coach</div>
                <div className="text-dark-text-muted">
                  <span className={getNameColorClass(coach.rating)}>{coach.name}</span> <span className="text-orange-400">(Rating: {coach.rating})</span>
                </div>
              </div>
            ) : (
              <div className="text-dark-text-muted/50">No coach assigned</div>
            )}
          </div>

          <button
            onClick={saveLines}
            disabled={saving}
            className="btn btn-primary w-full mt-6 text-lg py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Lines'}
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
}
