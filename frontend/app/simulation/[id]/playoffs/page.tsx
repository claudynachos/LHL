'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import DashboardLayout from '@/app/components/DashboardLayout';
import { PlayoffBracket, PlayoffSeries, Team } from '@/lib/types';

const teamLabel = (team: Team | null) => {
  if (!team) return 'TBD';
  return team.city;
};

export default function PlayoffsPage() {
  const params = useParams();
  const router = useRouter();
  const simulationId = params.id;
  const [bracket, setBracket] = useState<PlayoffBracket | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simulatingRound, setSimulatingRound] = useState(false);
  const [teams, setTeams] = useState<any[]>([]);
  
  // Stanley Cup winner animation state
  const [showCupAnimation, setShowCupAnimation] = useState(false);
  const [cupWinner, setCupWinner] = useState<{ city: string; name: string } | null>(null);
  const [animationTimer, setAnimationTimer] = useState(10);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const animationTimerRef = useRef<NodeJS.Timeout | null>(null);

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
      const response = await api.post(`/api/simulations/${simulationId}/playoffs/simulate-game`);
      
      // Check if playoffs just completed - backend returns cup_winner directly
      if (response.data.playoffs_complete && response.data.cup_winner) {
        const winner = response.data.cup_winner;
        console.log('Stanley Cup winner from API:', winner.city, winner.name);
        triggerCupAnimation(winner.city, winner.name);
        return;
      }
      
      // Reload bracket to get latest state
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
      
      // Check if playoffs just completed - backend returns cup_winner directly
      if (response.data.playoffs_complete && response.data.cup_winner) {
        const winner = response.data.cup_winner;
        console.log('Stanley Cup winner from API:', winner.city, winner.name);
        triggerCupAnimation(winner.city, winner.name);
        return; // Don't continue, animation will redirect
      }
      
      // Reload bracket to get latest state
      await loadBracket();
    } catch (error) {
      console.error('Failed to simulate playoff round', error);
      // Still reload bracket even on error to show current state
      await loadBracket();
    } finally {
      setSimulatingRound(false);
    }
  };
  
  const triggerCupAnimation = (city: string, name: string) => {
    setCupWinner({ city, name });
    setShowCupAnimation(true);
    setAnimationTimer(10);
    
    // Play celebratory audio
    if (!audioRef.current) {
      audioRef.current = new Audio('/HockeyNightinCanada.mp3');
      audioRef.current.volume = 1;
    }
    audioRef.current.play().catch(error => {
      console.error('Failed to play audio:', error);
    });
    
    // Start countdown timer with local variable to avoid React state closure issues
    let countdown = 10;
    animationTimerRef.current = setInterval(() => {
      countdown -= 1;
      setAnimationTimer(countdown);
      if (countdown <= 0) {
        // Time's up, clean up and redirect to dashboard
        if (animationTimerRef.current) {
          clearInterval(animationTimerRef.current);
          animationTimerRef.current = null;
        }
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current.currentTime = 0;
        }
        setShowCupAnimation(false);
        
        // Store that we're coming from playoffs completion for dashboard animation
        sessionStorage.setItem('seasonComplete', 'true');
        sessionStorage.setItem('cupWinner', `${city} ${name}`);
        
        // Redirect to dashboard
        router.push(`/simulation/${simulationId}`);
      }
    }, 1000);
  };
  
  const skipCupAnimation = () => {
    // Clean up
    if (animationTimerRef.current) {
      clearInterval(animationTimerRef.current);
      animationTimerRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setShowCupAnimation(false);
    
    // Store that we're coming from playoffs completion for dashboard animation
    sessionStorage.setItem('seasonComplete', 'true');
    sessionStorage.setItem('cupWinner', cupWinner ? `${cupWinner.city} ${cupWinner.name}` : '');
    
    // Redirect to dashboard
    router.push(`/simulation/${simulationId}`);
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationTimerRef.current) {
        clearInterval(animationTimerRef.current);
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

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
      <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden" style={{ minWidth: '280px' }}>
        <div className={`px-6 py-5 transition-colors ${
          higherWon
            ? 'bg-primary-500/20 font-semibold text-primary-400'
            : 'text-dark-text'
        }`}>
          <div className="flex items-center justify-between gap-8">
            <span className="font-medium text-xl">{teamLabel(higherTeam)}</span>
            <span className="font-mono font-bold text-2xl">{series.higher_seed_wins}</span>
          </div>
        </div>
        <div className={`px-6 py-5 border-t border-dark-border transition-colors ${
          lowerWon
            ? 'bg-primary-500/20 font-semibold text-primary-400'
            : 'text-dark-text'
        }`}>
          <div className="flex items-center justify-between gap-8">
            <span className="font-medium text-xl">{teamLabel(lowerTeam)}</span>
            <span className="font-mono font-bold text-2xl">{series.lower_seed_wins}</span>
          </div>
        </div>
      </div>
    );
  };

  const renderRound = (roundSeries: PlayoffSeries[], roundNum: number, roundKey: string) => {
    if (!roundSeries || roundSeries.length === 0) return null;

    // Group matchups into pairs for bracket structure
    const pairs: PlayoffSeries[][] = [];
    for (let i = 0; i < roundSeries.length; i += 2) {
      pairs.push(roundSeries.slice(i, i + 2));
    }

    return (
      <div className="flex flex-col gap-16" data-round-key={roundKey}>
        {pairs.map((pair, pairIdx) => (
          <div key={pairIdx} className="flex flex-col gap-3">
            {pair.map((series, seriesIdx) => (
              <div 
                key={series.id} 
                className="relative" 
                data-series-index={pairIdx * 2 + seriesIdx}
                data-series-id={series.id}
                ref={(el) => {
                  if (el) {
                    (el as any).__seriesId = series.id;
                  }
                }}
              >
                {renderMatchup(series)}
              </div>
            ))}
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
            // Check if THIS round should have connector lines going to the next round
            // Connector should be drawn from the round that has PAIRS of matchups feeding into the next round
            const nextActualRound = round + 1;
            const hasNextRound = conferenceSeries[nextActualRound] && conferenceSeries[nextActualRound].length > 0;
            const currentSeriesList = conferenceSeries[round] || [];
            const shouldDrawConnector = hasNextRound && currentSeriesList.length >= 2;
            
            return (
              <div key={round} className="flex-shrink-0 relative flex flex-col items-center">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-semibold text-dark-text">
                    {getRoundLabel(round, true)}
                  </h3>
                </div>
                <div className="relative flex items-center">
                  {renderRound(conferenceSeries[round], round, `${conferenceName}-round-${round}`)}
                  
                  {/* NHL-style bracket connector lines between rounds */}
                  {shouldDrawConnector && (
                    <div className={`absolute top-0 bottom-0 w-32 flex items-center ${
                      isEastern ? 'right-full' : 'left-full'
                    }`}>
                      <svg className="w-full h-full" style={{ overflow: 'visible' }}>
                        {(() => {
                          // Group matchups in pairs for bracket connections
                          const seriesList = conferenceSeries[round];
                          const pairs: [PlayoffSeries | undefined, PlayoffSeries | undefined][] = [];
                          for (let i = 0; i < seriesList.length; i += 2) {
                            pairs.push([seriesList[i], seriesList[i + 1]]);
                          }
                          
                          // Box dimensions (updated for larger boxes - px-6 py-5 = ~64px per row)
                          const boxHeight = 140; // Height of matchup box (2 rows * 64px + borders)
                          const gapWithinPair = 12; // Gap between matchups within a pair (gap-3)
                          const gapBetweenPairs = 64; // Gap between pairs (gap-16)
                          const pairHeight = boxHeight * 2 + gapWithinPair; // Height of one pair
                          
                          return pairs.map((pair, pairIdx) => {
                            const [series1, series2] = pair;
                            const bothComplete = series1?.status === 'complete' && series2?.status === 'complete';
                            
                            // Calculate Y positions for each matchup center within this pair
                            const pairStartY = pairIdx * (pairHeight + gapBetweenPairs);
                            const topY = pairStartY + (boxHeight / 2);
                            const bottomY = pairStartY + boxHeight + gapWithinPair + (boxHeight / 2);
                            const midY = (topY + bottomY) / 2;
                            
                            // X positions for bracket shape (w-32 = 128px)
                            // For Western: lines go from left (0) to right (128)
                            // For Eastern: lines go from right (128) to left (0) - but positioned on the LEFT of round 1
                            const xStart = isEastern ? 128 : 0;
                            const xMid = 64;
                            const xEnd = isEastern ? 0 : 128;
                            
                            const strokeColor = "#f97316";
                            const strokeWidth = 3;
                            
                            return (
                              <g key={`pair-${pairIdx}`}>
                                {/* TOP matchup: horizontal line, then vertical line going DOWN to midpoint */}
                                {series1?.status === 'complete' && (
                                  <>
                                    <line
                                      x1={xStart}
                                      y1={topY}
                                      x2={xMid}
                                      y2={topY}
                                      stroke={strokeColor}
                                      strokeWidth={strokeWidth}
                                      strokeLinecap="square"
                                    />
                                    <line
                                      x1={xMid}
                                      y1={topY}
                                      x2={xMid}
                                      y2={midY}
                                      stroke={strokeColor}
                                      strokeWidth={strokeWidth}
                                      strokeLinecap="square"
                                    />
                                  </>
                                )}
                                
                                {/* BOTTOM matchup: horizontal line, then vertical line going UP to midpoint */}
                                {series2?.status === 'complete' && (
                                  <>
                                    <line
                                      x1={xStart}
                                      y1={bottomY}
                                      x2={xMid}
                                      y2={bottomY}
                                      stroke={strokeColor}
                                      strokeWidth={strokeWidth}
                                      strokeLinecap="square"
                                    />
                                    <line
                                      x1={xMid}
                                      y1={bottomY}
                                      x2={xMid}
                                      y2={midY}
                                      stroke={strokeColor}
                                      strokeWidth={strokeWidth}
                                      strokeLinecap="square"
                                    />
                                  </>
                                )}
                                
                                {/* Horizontal line from midpoint to next round */}
                                {bothComplete && (
                                  <line
                                    x1={xMid}
                                    y1={midY}
                                    x2={xEnd}
                                    y2={midY}
                                    stroke={strokeColor}
                                    strokeWidth={strokeWidth}
                                    strokeLinecap="square"
                                  />
                                )}
                              </g>
                            );
                          });
                        })()}
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
      {/* Stanley Cup Winner Animation */}
      {showCupAnimation && cupWinner && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center">
          <div className="text-center animate-fade-in">
            <div className="text-6xl mb-6">🏆</div>
            <h1 className="text-5xl font-bold text-primary-500 mb-4 animate-pulse">
              STANLEY CUP CHAMPIONS
            </h1>
            <h2 className="text-4xl font-bold text-white mb-8">
              {cupWinner.city} {cupWinner.name}
            </h2>
            <p className="text-dark-text-muted mb-6">
              Redirecting to dashboard in {animationTimer} seconds...
            </p>
            <button
              onClick={skipCupAnimation}
              className="btn btn-secondary px-8 py-3"
            >
              Continue to Dashboard
            </button>
          </div>
        </div>
      )}
      
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
                <div className="flex gap-8 items-start justify-center">
                  {renderConferenceBracket(organizedBracket.western, 'Western')}
                  {renderConferenceBracket(organizedBracket.eastern, 'Eastern')}
                </div>

                {/* Stanley Cup Final - below conferences */}
                <div className="flex justify-center">
                  {organizedBracket.final ? (
                    <div className="card bg-gradient-to-br from-primary-500/20 to-primary-600/10 border-2 border-primary-500 max-w-lg">
                      <div className="text-center mb-4">
                        <h2 className="text-2xl font-bold text-primary-500 mb-1">STANLEY CUP FINAL</h2>
                        <div className="text-dark-text-muted text-sm">Round {maxRound}</div>
                      </div>
                      <div className="flex justify-center">
                        {renderMatchup(organizedBracket.final)}
                      </div>
                    </div>
                  ) : (
                    <div className="card bg-dark-surface/50 border border-dashed border-dark-border px-12 py-8">
                      <div className="text-center text-dark-text-muted">
                        <div className="text-lg font-semibold mb-1">Stanley Cup Final</div>
                        <div className="text-sm">Awaiting conference champions</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
