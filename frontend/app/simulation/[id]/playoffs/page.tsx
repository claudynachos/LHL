'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import DashboardLayout from '@/app/components/DashboardLayout';
import { PlayoffBracket, PlayoffSeries, Team } from '@/lib/types';

const teamLabel = (team: Team | null) => {
  if (!team) return 'TBD';
  return team.city;
};

export default function PlayoffsPage() {
  const params = useParams();
  const simulationId = params.id;
  const [bracket, setBracket] = useState<PlayoffBracket | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simulatingRound, setSimulatingRound] = useState(false);
  const [teams, setTeams] = useState<any[]>([]);

  const loadBracket = async () => {
    try {
      const response = await api.get(`/api/simulations/${simulationId}/playoffs`);
      setBracket(response.data);
    } catch (error) {
      console.error('Failed to load playoff bracket', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTeams = async () => {
    try {
      const response = await api.get(`/api/simulations/${simulationId}`);
      setTeams(response.data.teams || []);
    } catch (error) {
      console.error('Failed to load teams', error);
    }
  };

  useEffect(() => {
    loadBracket();
    loadTeams();
  }, []);

  const simulateNextGames = async () => {
    setSimulating(true);
    try {
      await api.post(`/api/simulations/${simulationId}/playoffs/simulate-game`);
      await loadBracket();
    } catch (error) {
      console.error('Failed to simulate playoff games', error);
      // Still reload bracket even on error to show current state
      await loadBracket();
    } finally {
      setSimulating(false);
    }
  };

  const simulateRound = async () => {
    setSimulatingRound(true);
    try {
      const response = await api.post(`/api/simulations/${simulationId}/playoffs/simulate-round`);
      await loadBracket();
      
      // If playoffs are complete, refresh the page to show updated status
      if (response.data.simulation_status === 'season') {
        // Reload the bracket and check if we should redirect or refresh
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    } catch (error) {
      console.error('Failed to simulate playoff round', error);
      // Still reload bracket even on error to show current state
      await loadBracket();
    } finally {
      setSimulatingRound(false);
    }
  };

  // Check if there are any active series
  const hasActiveSeries = bracket && Object.values(bracket.rounds).some((round: any) =>
    round.some((series: PlayoffSeries) => series.status === 'in_progress')
  );

  const rounds = bracket?.rounds ? Object.keys(bracket.rounds).map(Number).sort((a, b) => a - b) : [];
  
  // Filter out any invalid rounds and find the actual final round
  // The final round should be the one with teams from different conferences
  let maxRound = rounds.length > 0 ? Math.max(...rounds) : 0;
  let actualFinalRound = maxRound;
  
  if (bracket && maxRound > 0) {
    // Check each round from highest to lowest to find the actual final
    for (let round = maxRound; round >= 1; round--) {
      const roundSeries = bracket.rounds[String(round)] || [];
      const hasFinal = roundSeries.some((series: any) => {
        const higherTeam = series.higher_seed_team;
        const lowerTeam = series.lower_seed_team;
        return higherTeam?.conference && 
               lowerTeam?.conference && 
               higherTeam.conference !== lowerTeam.conference;
      });
      if (hasFinal) {
        actualFinalRound = round;
        break;
      }
    }
  }
  
  // Filter rounds to exclude any after the final
  const validRounds = rounds.filter(r => r <= actualFinalRound);
  maxRound = actualFinalRound;

  // Calculate teams per conference to determine number of rounds
  const calculateTeamsPerConference = () => {
    if (teams.length === 0) return 0;
    const easternTeams = teams.filter((t: any) => t.conference === 'Eastern').length;
    const westernTeams = teams.filter((t: any) => t.conference === 'Western').length;
    return Math.min(easternTeams, westernTeams);
  };

  const teamsPerConference = calculateTeamsPerConference();
  
  // Determine which round is Conference Final (last round before Stanley Cup Final)
  // If 2 teams per conference: Round 1 = Conference Final
  // If 4 teams per conference: Round 2 = Conference Final
  const getConferenceFinalRound = () => {
    if (teamsPerConference === 2) return 1;
    if (teamsPerConference === 4) return 2;
    return 0; // Unknown
  };

  const conferenceFinalRound = getConferenceFinalRound();

  // Organize series by conference and round
  const organizeBracket = () => {
    if (!bracket) return { eastern: {}, western: {}, final: null };

    const organized: {
      eastern: Record<number, PlayoffSeries[]>;
      western: Record<number, PlayoffSeries[]>;
      final: PlayoffSeries | null;
    } = {
      eastern: {},
      western: {},
      final: null
    };

    validRounds.forEach((round) => {
      const roundSeries = bracket.rounds[String(round)] || [];
      
      roundSeries.forEach((series: any) => {
        const higherTeam = series.higher_seed_team;
        const lowerTeam = series.lower_seed_team;
        const higherConference = higherTeam?.conference;
        const lowerConference = lowerTeam?.conference;
        const conference = series.conference || higherConference || lowerConference;
        
        // Check if this is the Stanley Cup Final
        // Final is when: it's the max round AND teams are from different conferences
        const isFinal = round === maxRound && 
          higherConference && 
          lowerConference && 
          higherConference !== lowerConference;
        
        if (isFinal) {
          organized.final = series;
        } else if (conference === 'Eastern') {
          if (!organized.eastern[round]) organized.eastern[round] = [];
          organized.eastern[round].push(series);
        } else if (conference === 'Western') {
          if (!organized.western[round]) organized.western[round] = [];
          organized.western[round].push(series);
        }
      });
    });

    return organized;
  };

  const organizedBracket = organizeBracket();

  const getRoundLabel = (round: number, isConference: boolean) => {
    if (isConference && round === conferenceFinalRound) {
      return 'Conference Final';
    }
    return `Round ${round}`;
  };

  const renderMatchup = (series: PlayoffSeries) => {
    const higherTeam = series.higher_seed_team;
    const lowerTeam = series.lower_seed_team;
    const higherWon = series.status === 'complete' && series.winner_team_id === series.higher_seed_team_id;
    const lowerWon = series.status === 'complete' && series.winner_team_id === series.lower_seed_team_id;

    return (
      <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
        <div className={`p-3 text-sm transition-colors ${
          higherWon
            ? 'bg-primary-500/20 font-semibold text-primary-400'
            : 'text-dark-text'
        }`}>
          <div className="flex items-center justify-between">
            <span className="font-medium">{teamLabel(higherTeam)}</span>
            <span className="font-mono font-bold">{series.higher_seed_wins}</span>
          </div>
        </div>
        <div className={`p-3 text-sm border-t border-dark-border transition-colors ${
          lowerWon
            ? 'bg-primary-500/20 font-semibold text-primary-400'
            : 'text-dark-text'
        }`}>
          <div className="flex items-center justify-between">
            <span className="font-medium">{teamLabel(lowerTeam)}</span>
            <span className="font-mono font-bold">{series.lower_seed_wins}</span>
          </div>
        </div>
      </div>
    );
  };

  const renderRound = (roundSeries: PlayoffSeries[], roundNum: number, roundKey: string) => {
    if (!roundSeries || roundSeries.length === 0) return null;

    return (
      <div className="flex flex-col gap-3" data-round-key={roundKey}>
        {roundSeries.map((series, seriesIdx) => (
          <div 
            key={series.id} 
            className="relative" 
            data-series-index={seriesIdx}
            data-series-id={series.id}
            ref={(el) => {
              if (el) {
                // Store element reference for connector calculation
                (el as any).__seriesId = series.id;
              }
            }}
          >
            {renderMatchup(series)}
          </div>
        ))}
      </div>
    );
  };

  const renderConferenceBracket = (conferenceSeries: Record<number, PlayoffSeries[]>, conferenceName: string) => {
    const conferenceRounds = Object.keys(conferenceSeries).map(Number).sort((a, b) => a - b);
    if (conferenceRounds.length === 0) return null;

    // For Eastern, reverse the rounds order so it flows right to left
    const displayRounds = conferenceName === 'Eastern' ? [...conferenceRounds].reverse() : conferenceRounds;
    const isEastern = conferenceName === 'Eastern';

    return (
      <div className="flex-1">
        <div className="card mb-6">
          <h2 className="text-2xl font-bold text-dark-text text-center">{conferenceName} Conference</h2>
        </div>
        <div className="flex gap-8 items-center justify-center overflow-x-auto pb-8">
          {displayRounds.map((round, roundIdx) => {
            const isLastRound = roundIdx === displayRounds.length - 1;
            const actualRoundIdx = isEastern ? displayRounds.length - 1 - roundIdx : roundIdx;
            const nextRound = displayRounds[roundIdx + 1];
            const nextRoundSeries = nextRound ? conferenceSeries[nextRound] : [];
            
            return (
              <div key={round} className="flex-shrink-0 relative flex flex-col items-center">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-semibold text-dark-text">
                    {getRoundLabel(round, true)}
                  </h3>
                </div>
                <div className="relative flex items-center">
                  {renderRound(conferenceSeries[round], round, `${conferenceName}-round-${round}`)}
                  
                  {/* Vertical connector lines between rounds */}
                  {!isLastRound && (
                    <div className={`absolute top-0 bottom-0 w-20 flex items-center ${
                      isEastern ? 'right-full' : 'left-full'
                    }`}>
                      <svg className="w-full h-full" style={{ overflow: 'visible' }}>
                        {conferenceSeries[round].map((series, idx) => {
                          if (series.status !== 'complete') return null;
                          
                          // Calculate positions based on actual rendered layout
                          // Each matchup box: 2 rows with p-3 (12px padding) + text-sm line height
                          // Actual rendered height might vary slightly, so we'll use a measured approach
                          // Matchup box approximate height: ~90px (2 rows × ~45px each)
                          // Gap between matchups: 12px (gap-3)
                          // Total spacing: ~102px per matchup
                          const boxHeight = 90; // Slightly adjusted to match actual rendered height
                          const gap = 12;
                          const totalSpacing = boxHeight + gap; // 102px
                          
                          // Calculate center Y position for each matchup
                          // Position from top: (idx * totalSpacing) + (boxHeight / 2)
                          const currentTop = (idx * totalSpacing) + (boxHeight / 2);
                          
                          // Find which matchup in next round this winner goes to
                          const nextMatchupIndex = Math.floor(idx / 2);
                          const nextTop = (nextMatchupIndex * totalSpacing) + (boxHeight / 2);
                          
                          // For Eastern (right to left), flip the connector
                          const xStart = isEastern ? 80 : 0;
                          const xMid = 40;
                          const xEnd = isEastern ? 0 : 80;
                          const cornerRadius = 10;
                          
                          // Create smooth path with rounded corners
                          let path = '';
                          const goingDown = currentTop < nextTop;
                          
                          if (isEastern) {
                            // Right to left flow
                            path = goingDown
                              ? `M ${xStart} ${currentTop} 
                                 L ${xMid + cornerRadius} ${currentTop}
                                 Q ${xMid} ${currentTop} ${xMid} ${currentTop + cornerRadius}
                                 L ${xMid} ${nextTop - cornerRadius}
                                 Q ${xMid} ${nextTop} ${xMid - cornerRadius} ${nextTop}
                                 L ${xEnd} ${nextTop}`
                              : `M ${xStart} ${currentTop} 
                                 L ${xMid + cornerRadius} ${currentTop}
                                 Q ${xMid} ${currentTop} ${xMid} ${currentTop - cornerRadius}
                                 L ${xMid} ${nextTop + cornerRadius}
                                 Q ${xMid} ${nextTop} ${xMid - cornerRadius} ${nextTop}
                                 L ${xEnd} ${nextTop}`;
                          } else {
                            // Left to right flow
                            path = goingDown
                              ? `M ${xStart} ${currentTop} 
                                 L ${xMid - cornerRadius} ${currentTop}
                                 Q ${xMid} ${currentTop} ${xMid} ${currentTop + cornerRadius}
                                 L ${xMid} ${nextTop - cornerRadius}
                                 Q ${xMid} ${nextTop} ${xMid + cornerRadius} ${nextTop}
                                 L ${xEnd} ${nextTop}`
                              : `M ${xStart} ${currentTop} 
                                 L ${xMid - cornerRadius} ${currentTop}
                                 Q ${xMid} ${currentTop} ${xMid} ${currentTop - cornerRadius}
                                 L ${xMid} ${nextTop + cornerRadius}
                                 Q ${xMid} ${nextTop} ${xMid + cornerRadius} ${nextTop}
                                 L ${xEnd} ${nextTop}`;
                          }
                          
                          return (
                            <g key={series.id}>
                              <path
                                d={path}
                                fill="none"
                                stroke="#f97316"
                                strokeWidth="3.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                style={{ 
                                  filter: 'drop-shadow(0 0 2px rgba(249, 115, 22, 0.4))'
                                }}
                              />
                            </g>
                          );
                        })}
                      </svg>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <div className="card mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-dark-text mb-2">Stanley Cup Playoffs {bracket?.season || ''}</h1>
              {bracket && (
                <div className="flex items-center gap-4 text-dark-text-muted">
                  <span>Season {bracket.season}</span>
                  <span>•</span>
                  <span className="capitalize">Status: {bracket.status}</span>
                </div>
              )}
            </div>
            {hasActiveSeries && (
              <div className="flex gap-3">
                <button
                  onClick={simulateNextGames}
                  disabled={simulating || simulatingRound}
                  className="btn btn-primary px-6 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {simulating ? 'Simulating...' : 'Simulate Next Game'}
                </button>
                <button
                  onClick={simulateRound}
                  disabled={simulating || simulatingRound}
                  className="btn btn-primary px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {simulatingRound ? 'Simulating...' : 'Simulate Round'}
                </button>
              </div>
            )}
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center min-h-[300px]">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-dark-text-muted">Loading bracket...</p>
            </div>
          </div>
        ) : (
          <>
            {validRounds.length === 0 && (
              <div className="card">
                <p className="text-dark-text-muted text-center">No playoff bracket found yet.</p>
              </div>
            )}

            {validRounds.length > 0 && (
              <div className="space-y-8">
                {/* Conference Brackets */}
                <div className="flex gap-8 items-start">
                  {renderConferenceBracket(organizedBracket.western, 'Western')}
                  {renderConferenceBracket(organizedBracket.eastern, 'Eastern')}
                </div>

                {/* Stanley Cup Final */}
                {organizedBracket.final && (
                  <div className="flex justify-center">
                    <div className="card bg-gradient-to-br from-primary-500/20 to-primary-600/10 border-2 border-primary-500 max-w-md w-full">
                      <div className="text-center mb-6">
                        <h2 className="text-3xl font-bold text-primary-500 mb-2">STANLEY CUP FINAL</h2>
                        <div className="text-dark-text-muted">Round {maxRound}</div>
                      </div>
                      <div className="flex justify-center">
                        <div className="w-full max-w-xs">
                          {renderMatchup(organizedBracket.final)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
