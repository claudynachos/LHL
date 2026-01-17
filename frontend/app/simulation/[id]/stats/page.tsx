'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import { PlayerStats } from '@/lib/types';
import DashboardLayout from '@/app/components/DashboardLayout';

// Helper function to get name color class based on rating (gold for 100+, silver for 95-100)
const getNameColorClass = (rating: number | undefined): string => {
  if (rating === undefined || rating === null) return '';
  if (rating > 100) return 'text-amber-400 drop-shadow-[0_0_3px_rgba(251,191,36,0.6)]'; // Gold with glow
  if (rating >= 95) return 'text-slate-300 drop-shadow-[0_0_3px_rgba(203,213,225,0.5)]'; // Silver with glow
  return ''; // Default - no special styling
};

export default function StatsPage() {
  const params = useParams();
  const simulationId = params.id;

  const [stats, setStats] = useState<PlayerStats[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('points');
  const [viewMode, setViewMode] = useState<'skaters' | 'goalies'>('skaters');
  const [positionFilter, setPositionFilter] = useState<string>('all'); // 'all', 'forward', 'defenseman'
  const [teamFilter, setTeamFilter] = useState<string>('all'); // 'all' or team_id
  const [gameType, setGameType] = useState<'regular' | 'playoff' | 'all'>('regular'); // 'regular', 'playoff', or 'all'

  useEffect(() => {
    loadTeams();
  }, []);

  useEffect(() => {
    if (teams.length > 0) {
      loadStats();
    }
  }, [positionFilter, teamFilter, viewMode, gameType]);

  const loadTeams = async () => {
    try {
      const response = await api.get(`/api/simulations/${simulationId}`);
      const teamsList = response.data.teams;
      setTeams(teamsList);
      
      // Set default team to user's team
      const userTeam = teamsList.find((team: any) => team.user_controlled);
      if (userTeam) {
        setTeamFilter(userTeam.id.toString());
      }
    } catch (error) {
      console.error('Failed to load teams', error);
    }
  };

  const loadStats = async () => {
    try {
      setLoading(true);
      const queryParams: Record<string, string> = {};
      
      if (viewMode === 'skaters') {
        if (positionFilter === 'forward' || positionFilter === 'defenseman') {
          queryParams.position_filter = positionFilter;
        }
      }
      
      if (teamFilter !== 'all') {
        queryParams.team_id = teamFilter;
      }
      
      // Add game type filter (defaults to 'regular' which excludes playoffs)
      if (gameType !== 'all') {
        queryParams.game_type = gameType;
      }
      
      const queryString = new URLSearchParams(queryParams).toString();
      const url = `/api/stats/season/${simulationId}${queryString ? '?' + queryString : ''}`;
      const response = await api.get(url);
      setStats(response.data.stats);
    } catch (error) {
      console.error('Failed to load stats', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter stats by position
  const skaterStats = stats.filter(s => s.position !== 'G');
  const goalieStats = stats.filter(s => s.position === 'G');

  const sortedStats = [...(viewMode === 'skaters' ? skaterStats : goalieStats)].sort((a, b) => {
    const aVal = (a as any)[sortBy] || 0;
    const bVal = (b as any)[sortBy] || 0;
    return bVal - aVal;
  });

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-dark-text-muted">Loading stats...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <div className="card mb-4">
          <h1 className="text-3xl font-bold text-dark-text">Season Stats Leaders</h1>
        </div>

        <div className="flex gap-4">
          {/* Sidebar filters */}
          <div className="w-48 flex-shrink-0">
            <div className="card">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">View</label>
                  <div className="flex flex-col gap-2">
                    <button
                      className={`px-3 py-2 rounded text-sm ${viewMode === 'skaters' ? 'bg-primary-500 text-white' : 'bg-dark-surface text-dark-text'}`}
                      onClick={() => {
                        setViewMode('skaters');
                        setSortBy('points');
                      }}
                    >
                      Skaters
                    </button>
                    <button
                      className={`px-3 py-2 rounded text-sm ${viewMode === 'goalies' ? 'bg-primary-500 text-white' : 'bg-dark-surface text-dark-text'}`}
                      onClick={() => {
                        setViewMode('goalies');
                        setSortBy('save_percentage');
                      }}
                    >
                      Goalies
                    </button>
                  </div>
                </div>
                
                {viewMode === 'skaters' && (
                  <div>
                    <label className="block text-sm font-medium text-dark-text mb-2">Position</label>
                    <select
                      className="input w-full text-sm"
                      value={positionFilter}
                      onChange={(e) => setPositionFilter(e.target.value)}
                    >
                      <option value="all">All Positions</option>
                      <option value="forward">Forwards</option>
                      <option value="defenseman">Defensemen</option>
                    </select>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">Team</label>
                  <select
                    className="input w-full text-sm"
                    value={teamFilter}
                    onChange={(e) => setTeamFilter(e.target.value)}
                  >
                    <option value="all">All Teams</option>
                    {teams.map((team) => (
                      <option key={team.id} value={team.id.toString()}>
                        {team.city} {team.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">Game Type</label>
                  <select
                    className="input w-full text-sm"
                    value={gameType}
                    onChange={(e) => setGameType(e.target.value as 'regular' | 'playoff' | 'all')}
                  >
                    <option value="regular">Regular Season</option>
                    <option value="playoff">Playoffs</option>
                    <option value="all">All Games</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2">Sort By</label>
                  <select
                    className="input w-full text-sm"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                  >
                    {viewMode === 'skaters' ? (
                      <>
                        <option value="points">Points</option>
                        <option value="goals">Goals</option>
                        <option value="assists">Assists</option>
                        <option value="plus_minus">Plus/Minus</option>
                        <option value="hits">Hits</option>
                        <option value="blocks">Block Shots</option>
                      </>
                    ) : (
                      <>
                        <option value="save_percentage">Save %</option>
                        <option value="wins">Wins</option>
                        <option value="goals_against_average">GAA</option>
                        <option value="saves">Saves</option>
                        <option value="games_played">Games</option>
                      </>
                    )}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Main content area with table */}
          <div className="flex-1 min-w-0">
            <div className="card">
              <div className="overflow-auto">
                <table className="w-full">
                  <thead className="bg-dark-surface">
                    {viewMode === 'skaters' ? (
                      <tr>
                        <th className="p-3 text-left text-dark-text">Rank</th>
                        <th className="p-3 text-left text-dark-text">Player</th>
                        <th className="p-3 text-center text-dark-text">Pos</th>
                        <th className="p-3 text-left text-dark-text">Team</th>
                        <th className="p-3 text-center text-dark-text">GP</th>
                        <th className="p-3 text-center text-dark-text">G</th>
                        <th className="p-3 text-center text-dark-text">A</th>
                        <th className="p-3 text-center text-dark-text">PTS</th>
                        <th className="p-3 text-center text-dark-text">+/-</th>
                        <th className="p-3 text-center text-dark-text">Hits</th>
                        <th className="p-3 text-center text-dark-text">Block Shots</th>
                      </tr>
                    ) : (
                      <tr>
                        <th className="p-3 text-left text-dark-text">Rank</th>
                        <th className="p-3 text-left text-dark-text">Player</th>
                        <th className="p-3 text-left text-dark-text">Team</th>
                        <th className="p-3 text-center text-dark-text">GP</th>
                        <th className="p-3 text-center text-dark-text">W</th>
                        <th className="p-3 text-center text-dark-text">SV</th>
                        <th className="p-3 text-center text-dark-text">SA</th>
                        <th className="p-3 text-center text-dark-text">GA</th>
                        <th className="p-3 text-center text-dark-text">SV%</th>
                        <th className="p-3 text-center text-dark-text">GAA</th>
                      </tr>
                    )}
                  </thead>
                  <tbody>
                    {sortedStats.map((stat, idx) => (
                      <tr key={stat.player_id} className="border-b border-dark-border hover:bg-dark-surface">
                        <td className="p-3 font-bold text-dark-text">{idx + 1}</td>
                        <td className={`p-3 font-medium ${getNameColorClass(stat.player_overall) || 'text-dark-text'}`}>{stat.player_name}</td>
                        {viewMode === 'skaters' && (
                          <td className="p-3 text-center text-dark-text-muted">{stat.position}</td>
                        )}
                        <td className="p-3 text-dark-text">{stat.team_name || '-'}</td>
                        {viewMode === 'skaters' ? (
                          <>
                            <td className="p-3 text-center text-dark-text">{stat.games_played}</td>
                            <td className="p-3 text-center text-dark-text">{stat.goals}</td>
                            <td className="p-3 text-center text-dark-text">{stat.assists}</td>
                            <td className="p-3 text-center font-bold text-dark-text">{stat.points}</td>
                            <td className={`p-3 text-center ${stat.plus_minus >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {stat.plus_minus >= 0 ? '+' : ''}{stat.plus_minus}
                            </td>
                            <td className="p-3 text-center text-dark-text">{stat.hits}</td>
                            <td className="p-3 text-center text-dark-text">{stat.blocks}</td>
                          </>
                        ) : (
                          <>
                            <td className="p-3 text-center text-dark-text">{stat.games_played}</td>
                            <td className="p-3 text-center text-dark-text">
                              {(stat as any).wins !== null && (stat as any).wins !== undefined ? (stat as any).wins : '-'}
                            </td>
                            <td className="p-3 text-center text-dark-text">{stat.saves || 0}</td>
                            <td className="p-3 text-center text-dark-text">{stat.shots_against || 0}</td>
                            <td className="p-3 text-center text-dark-text">{stat.goals_against || 0}</td>
                            <td className="p-3 text-center font-bold text-dark-text">
                              {stat.save_percentage !== null && stat.save_percentage !== undefined 
                                ? stat.save_percentage.toFixed(3) 
                                : '-'}
                            </td>
                            <td className="p-3 text-center text-dark-text">
                              {stat.goals_against_average !== null && stat.goals_against_average !== undefined
                                ? stat.goals_against_average.toFixed(2)
                                : '-'}
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
