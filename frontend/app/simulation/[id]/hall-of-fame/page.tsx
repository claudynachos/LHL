'use client';

import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
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

type TabType = 'stats' | 'trophies' | 'ranking';

export default function HallOfFamePage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const simulationId = params.id;
  
  // Read initial tab from URL if provided
  const urlTab = searchParams.get('tab') as TabType | null;
  const [activeTab, setActiveTab] = useState<TabType>(urlTab || 'stats');
  
  // Stats tab state
  const [stats, setStats] = useState<PlayerStats[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('points');
  const [viewMode, setViewMode] = useState<'skaters' | 'goalies'>('skaters');
  const [positionFilter, setPositionFilter] = useState<string>('all');
  const [teamFilter, setTeamFilter] = useState<string>('all');
  const [gameType, setGameType] = useState<'regular' | 'playoff' | 'all'>('regular');
  
  // Trophies tab state
  const [trophies, setTrophies] = useState<Record<number, any[]>>({});
  const [trophyLoading, setTrophyLoading] = useState(false);
  const [trophySeasonFilter, setTrophySeasonFilter] = useState<string>('all');
  const [trophyTypeFilter, setTrophyTypeFilter] = useState<string>('all');
  const [trophyTeamFilter, setTrophyTeamFilter] = useState<string>('all');
  
  // Ranking tab state
  const [ranking, setRanking] = useState<any[]>([]);
  const [rankingLoading, setRankingLoading] = useState(false);

  useEffect(() => {
    loadTeams();
  }, []);

  useEffect(() => {
    if (activeTab === 'stats') {
      loadStats();
    } else if (activeTab === 'trophies') {
      loadTrophies();
    } else if (activeTab === 'ranking') {
      loadRanking();
    }
  }, [activeTab, viewMode, gameType, trophySeasonFilter, trophyTypeFilter, trophyTeamFilter]);

  const loadTeams = async () => {
    try {
      const response = await api.get(`/api/simulations/${simulationId}`);
      const teamsList = response.data.teams;
      setTeams(teamsList);
    } catch (error) {
      console.error('Failed to load teams', error);
    }
  };

  const loadStats = async () => {
    try {
      setLoading(true);
      const queryParams: Record<string, string> = {};
      
      if (gameType !== 'all') {
        queryParams.game_type = gameType;
      }
      
      const queryString = new URLSearchParams(queryParams).toString();
      const url = `/api/stats/all-time/${simulationId}${queryString ? '?' + queryString : ''}`;
      const response = await api.get(url);
      setStats(response.data.stats || []);
    } catch (error: any) {
      console.error('Failed to load Hall of Fame stats', error);
      setStats([]);
      // Show error message to user
      if (error.response?.data?.error) {
        console.error('API Error:', error.response.data.error);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadTrophies = async () => {
    try {
      setTrophyLoading(true);
      const queryParams: Record<string, string> = {};
      
      if (trophySeasonFilter !== 'all') {
        queryParams.season = trophySeasonFilter;
      }
      
      if (trophyTypeFilter !== 'all') {
        queryParams.trophy_type = trophyTypeFilter;
      }
      
      if (trophyTeamFilter !== 'all') {
        queryParams.team_id = trophyTeamFilter;
      }
      
      const queryString = new URLSearchParams(queryParams).toString();
      const url = `/api/trophies/${simulationId}${queryString ? '?' + queryString : ''}`;
      const response = await api.get(url);
      setTrophies(response.data.trophies_by_season || {});
    } catch (error) {
      console.error('Failed to load trophies', error);
    } finally {
      setTrophyLoading(false);
    }
  };

  const loadRanking = async () => {
    try {
      setRankingLoading(true);
      const response = await api.get(`/api/trophies/simulation-ranking/${simulationId}`);
      setRanking(response.data.ranking || []);
    } catch (error) {
      console.error('Failed to load simulation ranking', error);
    } finally {
      setRankingLoading(false);
    }
  };

  // Filter stats by position
  const skaterStats = stats.filter(s => s.position !== 'G');
  const goalieStats = stats.filter(s => s.position === 'G');

  // Apply client-side filters
  let filteredStats = viewMode === 'skaters' ? skaterStats : goalieStats;
  
  if (viewMode === 'skaters' && positionFilter !== 'all') {
    filteredStats = filteredStats.filter(s => {
      if (positionFilter === 'forward') {
        return s.position === 'C' || s.position === 'LW' || s.position === 'RW';
      } else if (positionFilter === 'defenseman') {
        return s.position === 'D';
      }
      return true;
    });
  }

  if (teamFilter !== 'all') {
    filteredStats = filteredStats.filter(s => {
      const teamId = (s as any).team_id;
      return teamId && teamId.toString() === teamFilter;
    });
  }

  const sortedStats = [...filteredStats].sort((a, b) => {
    const aVal = (a as any)[sortBy] || 0;
    const bVal = (b as any)[sortBy] || 0;
    return bVal - aVal;
  });

  // Get all seasons for trophy filter
  const allSeasons = Object.keys(trophies).map(Number).sort((a, b) => b - a);

  const renderStatsTab = () => (
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
                    <option value="games_played">Games Played</option>
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
          {loading ? (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-dark-text-muted">Loading statistics...</p>
              </div>
            </div>
          ) : (
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
                  {sortedStats.length === 0 ? (
                    <tr>
                      <td colSpan={viewMode === 'skaters' ? 11 : 10} className="p-8 text-center text-dark-text-muted">
                        No statistics available yet
                      </td>
                    </tr>
                  ) : (
                    sortedStats.map((stat, idx) => (
                      <tr key={stat.player_id} className="border-b border-dark-border hover:bg-dark-surface">
                        <td className="p-3 font-bold text-dark-text">{idx + 1}</td>
                        <td className={`p-3 font-medium ${getNameColorClass(stat.player_overall) || 'text-dark-text'}`}>{stat.player_name}</td>
                        {viewMode === 'skaters' && (
                          <td className="p-3 text-center text-dark-text-muted">{stat.position}</td>
                        )}
                        <td className="p-3 text-dark-text">{(stat as any).team_name || '-'}</td>
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
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderTrophiesTab = () => (
    <div className="flex gap-4">
      {/* Sidebar filters */}
      <div className="w-48 flex-shrink-0">
        <div className="card">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-text mb-2">Season</label>
              <select
                className="input w-full text-sm"
                value={trophySeasonFilter}
                onChange={(e) => setTrophySeasonFilter(e.target.value)}
              >
                <option value="all">All Seasons</option>
                {allSeasons.map((season) => (
                  <option key={season} value={season.toString()}>
                    Season {season}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-dark-text mb-2">Award Type</label>
              <select
                className="input w-full text-sm"
                value={trophyTypeFilter}
                onChange={(e) => setTrophyTypeFilter(e.target.value)}
              >
                <option value="all">All Awards</option>
                <option value="team">Team Awards</option>
                <option value="individual">Individual Awards</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-dark-text mb-2">Team</label>
              <select
                className="input w-full text-sm"
                value={trophyTeamFilter}
                onChange={(e) => setTrophyTeamFilter(e.target.value)}
              >
                <option value="all">All Teams</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id.toString()}>
                    {team.city} {team.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 min-w-0">
        <div className="card">
          {trophyLoading ? (
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-dark-text-muted">Loading trophies...</p>
              </div>
            </div>
          ) : Object.keys(trophies).length === 0 ? (
            <div className="p-8 text-center text-dark-text-muted">
              No trophies awarded yet
            </div>
          ) : (
            <div className="space-y-6">
              {allSeasons.map((season) => (
                <div key={season} className="border-b border-dark-border pb-6 last:border-b-0">
                  <h3 className="text-xl font-bold text-dark-text mb-4">Season {season}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {trophies[season].map((trophy: any) => (
                      <div key={trophy.id} className="bg-dark-surface p-4 rounded border border-dark-border">
                        <div className="font-bold text-primary-500 mb-2">{trophy.trophy_name}</div>
                        {trophy.trophy_type === 'team' ? (
                          <div className="text-dark-text">
                            <div className="font-medium">{trophy.team_city} {trophy.team_name}</div>
                          </div>
                        ) : (
                          <div className="text-dark-text">
                            <div className="font-medium">{trophy.player_name}</div>
                            {trophy.team_name && (
                              <div className="text-sm text-dark-text-muted">{trophy.team_city} {trophy.team_name}</div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderRankingTab = () => (
    <div className="card">
      {rankingLoading ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-dark-text-muted">Loading ranking...</p>
          </div>
        </div>
      ) : ranking.length === 0 ? (
        <div className="p-8 text-center text-dark-text-muted">
          No Stanley Cup winners yet
        </div>
      ) : (
        <div className="overflow-auto">
          <table className="w-full">
            <thead className="bg-dark-surface">
              <tr>
                <th className="p-3 text-left text-dark-text">Rank</th>
                <th className="p-3 text-left text-dark-text">Team</th>
                <th className="p-3 text-center text-dark-text">Stanley Cups</th>
              </tr>
            </thead>
            <tbody>
              {ranking.map((team) => (
                <tr key={team.team_id} className="border-b border-dark-border hover:bg-dark-surface">
                  <td className="p-3 font-bold text-dark-text">{team.rank}</td>
                  <td className="p-3 font-medium text-dark-text">{team.team_city} {team.team_name}</td>
                  <td className="p-3 text-center font-bold text-primary-500">{team.stanley_cups}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );


  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <div className="card mb-4">
          <h1 className="text-3xl font-bold text-dark-text">Hall of Fame</h1>
          <p className="text-dark-text-muted mt-2">All-time career statistics, trophies, and rankings</p>
        </div>

        {/* Tabs */}
        <div className="card mb-4">
          <div className="flex gap-2 border-b border-dark-border">
            <button
              className={`px-4 py-2 font-medium ${
                activeTab === 'stats'
                  ? 'text-primary-500 border-b-2 border-primary-500'
                  : 'text-dark-text-muted hover:text-dark-text'
              }`}
              onClick={() => setActiveTab('stats')}
            >
              Stats
            </button>
            <button
              className={`px-4 py-2 font-medium ${
                activeTab === 'trophies'
                  ? 'text-primary-500 border-b-2 border-primary-500'
                  : 'text-dark-text-muted hover:text-dark-text'
              }`}
              onClick={() => setActiveTab('trophies')}
            >
              Trophies
            </button>
            <button
              className={`px-4 py-2 font-medium ${
                activeTab === 'ranking'
                  ? 'text-primary-500 border-b-2 border-primary-500'
                  : 'text-dark-text-muted hover:text-dark-text'
              }`}
              onClick={() => setActiveTab('ranking')}
            >
              Simulation Ranking
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'stats' && renderStatsTab()}
        {activeTab === 'trophies' && renderTrophiesTab()}
        {activeTab === 'ranking' && renderRankingTab()}
      </div>
    </DashboardLayout>
  );
}
