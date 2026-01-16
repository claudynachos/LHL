'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { Player, Team } from '@/lib/types';
import DashboardLayout from '@/app/components/DashboardLayout';
import { useModal } from '@/app/components/ModalContext';

const USER_PICK_TIME = 120; // 2 minutes in seconds
const AI_PICK_TIME = 20; // 20 seconds

export default function DraftPage() {
  const router = useRouter();
  const params = useParams();
  const simulationId = params.id;
  const { showAlert, showConfirm } = useModal();

  const [availablePlayers, setAvailablePlayers] = useState<Player[]>([]);
  const [availableCoaches, setAvailableCoaches] = useState<any[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [currentPick, setCurrentPick] = useState<any>(null);
  const [userTeam, setUserTeam] = useState<Team | null>(null);
  const [userRoster, setUserRoster] = useState<Player[]>([]);
  const [userLines, setUserLines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all'); // all, skaters, goalies, coaches
  const [sortBy, setSortBy] = useState<string>('overall');
  const [timer, setTimer] = useState<number>(0);
  const [isCoachesRound, setIsCoachesRound] = useState(false);
  const [showLotteryModal, setShowLotteryModal] = useState(false);
  const [lotteryOrder, setLotteryOrder] = useState<any[]>([]);
  const [lotteryRevealed, setLotteryRevealed] = useState<number>(0);
  const [lotteryTimer, setLotteryTimer] = useState<number>(0);
  const [draftHistory, setDraftHistory] = useState<any[]>([]);
  const [userCoach, setUserCoach] = useState<any>(null);
  const [isAutoPicking, setIsAutoPicking] = useState(false);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pickStartTimeRef = useRef<number>(Date.now());
  const isProcessingAIPickRef = useRef<boolean>(false); // Prevent multiple simultaneous AI picks
  const lotteryAnimationRef = useRef<NodeJS.Timeout[]>([]);
  const lotteryTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lotteryStartTimeRef = useRef<number>(0);
  const lotteryCurrentRevealedRef = useRef<number>(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    loadDraftData();
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      if (lotteryAnimationRef.current && lotteryAnimationRef.current.length > 0) {
        lotteryAnimationRef.current.forEach(timeoutId => {
          clearTimeout(timeoutId);
        });
        lotteryAnimationRef.current = [];
      }
      if (lotteryTimerRef.current) {
        clearInterval(lotteryTimerRef.current);
        lotteryTimerRef.current = null;
      }
      // Clean up audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    // Start timer when pick changes (only if lottery modal is not showing)
    if (currentPick && !showLotteryModal) {
      startTimer();
    }
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [currentPick, showLotteryModal]);

  // Stop audio when lottery modal closes
  useEffect(() => {
    if (!showLotteryModal && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }, [showLotteryModal]);

  // Debug: Track roster changes
  useEffect(() => {
    console.log('Roster state changed:', userRoster.length, 'players');
    const defensemen = userRoster.filter(p => p.position === 'D');
    console.log('Defensemen in state:', defensemen.length, defensemen.map(p => p.name));
  }, [userRoster]);

  const startTimer = () => {
    // Clear any existing timer first
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }

    // Don't start timer if we're processing an AI pick
    if (isProcessingAIPickRef.current) {
      return;
    }

    if (!currentPick) {
      return;
    }

    const timeLimit = currentPick.is_user_team ? USER_PICK_TIME : AI_PICK_TIME;
    const currentPickId = currentPick.pick; // Store the pick number to verify it hasn't changed
    
    setTimer(timeLimit);
    pickStartTimeRef.current = Date.now();

    timerIntervalRef.current = setInterval(() => {
      // Verify the current pick hasn't changed (another pick might have been made)
      if (!currentPick || currentPick.pick !== currentPickId) {
        if (timerIntervalRef.current) {
          clearInterval(timerIntervalRef.current);
          timerIntervalRef.current = null;
        }
        return;
      }

      const elapsed = Math.floor((Date.now() - pickStartTimeRef.current) / 1000);
      const remaining = Math.max(0, timeLimit - elapsed);
      setTimer(remaining);

      if (remaining === 0 && !isAutoPicking && !isProcessingAIPickRef.current) {
        // Double-check the pick hasn't changed
        if (!currentPick || currentPick.pick !== currentPickId) {
          if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
          }
          return;
        }

        if (currentPick.is_user_team) {
          // Auto-pick for user if timer expires
          setIsAutoPicking(true);
          makePick().finally(() => {
            setIsAutoPicking(false);
          });
        } else {
          // Auto-pick for AI if timer expires
          // Clear the interval immediately to prevent multiple calls
          if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
          }
          handleSimNextAI();
        }
      }
    }, 100);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const loadDraftData = async () => {
    try {
      // Load simulation and teams
      const simResponse = await api.get(`/api/simulations/${simulationId}`);
      const teamsData = simResponse.data.teams;
      setTeams(teamsData);
      
      // Find user team
      const userTeamData = teamsData.find((t: Team) => t.user_controlled);
      if (userTeamData) {
        setUserTeam(userTeamData);
        loadUserRoster(userTeamData.id);
      }

      // Load all players
      const playersResponse = await api.get('/api/players/');
      setAvailablePlayers(playersResponse.data.players || []);

      // Load coaches
      const coachesResponse = await api.get('/api/players/coaches');
      setAvailableCoaches(coachesResponse.data.coaches || []);

      // Get current pick info
      const pickResponse = await api.get(`/api/simulations/${simulationId}/draft/current`);
      
      // Load draft history
      loadDraftHistory();
      
      // If draft is complete, ensure lines are loaded
      if (pickResponse.data?.draft_complete && userTeamData) {
        // Small delay to ensure backend has auto-populated lines
        setTimeout(() => {
          loadUserRoster(userTeamData.id);
        }, 1000);
      }
      
      // Check if draft has started (pick > 1 means draft started, pick === 1 means first pick)
      if (pickResponse.data && !pickResponse.data.draft_complete && pickResponse.data.pick === 1) {
        // Show lottery modal before first pick
        const lotteryResponse = await api.get(`/api/simulations/${simulationId}/draft/lottery-order`);
        const order = lotteryResponse.data.lottery_order || [];
        setLotteryOrder(order);
        setShowLotteryModal(true);
        // Start animation with the order data directly
        if (order.length > 0) {
          startLotteryAnimationWithOrder(order);
        }
      } else {
        // Draft already started, load current pick
        setCurrentPick(pickResponse.data);
        setIsCoachesRound(pickResponse.data?.round === 21);
        await refreshAvailableEntities();
      }
    } catch (error) {
      console.error('Failed to load draft data', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDraftHistory = async () => {
    try {
      // Add cache busting to ensure we get fresh data
      const response = await api.get(`/api/simulations/${simulationId}/draft/history?t=${Date.now()}`);
      const history = response.data.history || [];
      setDraftHistory(history);
      console.log('Draft history loaded:', history.length, 'picks');
      // Log last few picks for debugging
      if (history.length > 0) {
        const lastPicks = history.slice(-5);
        lastPicks.forEach((pick: any) => {
          const player = pick.player?.name || 'N/A';
          const coach = pick.coach?.name || 'N/A';
          const picked = player !== 'N/A' ? player : (coach !== 'N/A' ? coach : 'EMPTY');
          console.log(`  R${pick.round} P${pick.pick}: ${pick.team_name} - ${picked}`);
        });
      }
    } catch (error) {
      console.error('Failed to load draft history', error);
    }
  };

  const skipLotteryAnimation = () => {
    // Clear all timeouts
    if (lotteryAnimationRef.current.length > 0) {
      lotteryAnimationRef.current.forEach(timeoutId => clearTimeout(timeoutId));
      lotteryAnimationRef.current = [];
    }
    if (lotteryTimerRef.current) {
      clearInterval(lotteryTimerRef.current);
      lotteryTimerRef.current = null;
    }
    
    // Immediately reveal all teams
    lotteryCurrentRevealedRef.current = lotteryOrder.length;
    setLotteryRevealed(lotteryOrder.length);
    setLotteryTimer(0);
    
    // Close modal after a brief delay
    setTimeout(() => {
      setShowLotteryModal(false);
      // Stop audio when modal closes
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      updateCurrentPick();
    }, 500);
  };

  const startLotteryAnimationWithOrder = (order: any[]) => {
    // Clear any existing timeouts
    if (lotteryAnimationRef.current.length > 0) {
      lotteryAnimationRef.current.forEach(timeoutId => clearTimeout(timeoutId));
      lotteryAnimationRef.current = [];
    }
    if (lotteryTimerRef.current) {
      clearInterval(lotteryTimerRef.current);
      lotteryTimerRef.current = null;
    }
    
    // Start playing the audio
    if (!audioRef.current) {
      audioRef.current = new Audio('/HockeyNightinCanada.mp3');
      audioRef.current.loop = true;
      audioRef.current.volume = isMuted ? 0 : 1;
    }
    audioRef.current.play().catch(error => {
      console.error('Failed to play audio:', error);
    });
    
    setLotteryRevealed(0);
    setLotteryTimer(5); // Start with 5 seconds
    lotteryStartTimeRef.current = Date.now();
    lotteryCurrentRevealedRef.current = 0;
    
    // Minimum 5 seconds per team reveal
    const delayPerTeam = 5000; // 5 seconds in milliseconds
    
    if (order.length === 0) {
      // No teams, skip animation
      setShowLotteryModal(false);
      updateCurrentPick();
      return;
    }
    
    // Start countdown timer that shows time until next reveal
    lotteryTimerRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - lotteryStartTimeRef.current) / 1000);
      const currentRevealed = lotteryCurrentRevealedRef.current;
      
      if (currentRevealed >= order.length) {
        // All revealed, clear timer
        if (lotteryTimerRef.current) {
          clearInterval(lotteryTimerRef.current);
          lotteryTimerRef.current = null;
        }
        setLotteryTimer(0);
        return;
      }
      
      const nextRevealTime = (currentRevealed + 1) * 5; // Next reveal at (currentRevealed + 1) * 5 seconds
      const timeUntilNext = Math.max(0, nextRevealTime - elapsed);
      setLotteryTimer(timeUntilNext);
    }, 100);
    
    // Reveal teams one by one, starting after 5 seconds
    for (let i = 0; i < order.length; i++) {
      const timeoutId = setTimeout(() => {
        lotteryCurrentRevealedRef.current = i + 1;
        setLotteryRevealed(i + 1);
        
        // If this is the last team, clear timer and close modal after a delay
        if (i === order.length - 1) {
          if (lotteryTimerRef.current) {
            clearInterval(lotteryTimerRef.current);
            lotteryTimerRef.current = null;
          }
          setLotteryTimer(0);
          
          const closeTimeout = setTimeout(() => {
            setShowLotteryModal(false);
            // Stop audio when modal closes
            if (audioRef.current) {
              audioRef.current.pause();
              audioRef.current.currentTime = 0;
            }
            updateCurrentPick();
          }, delayPerTeam + 1000); // Wait after last reveal before closing
          lotteryAnimationRef.current.push(closeTimeout);
        }
      }, (i + 1) * delayPerTeam); // Each reveal happens after (i+1) * 5 seconds
      lotteryAnimationRef.current.push(timeoutId);
    }
  };

  const loadUserRoster = async (teamId: number, retryCount: number = 0) => {
    try {
      const response = await api.get(`/api/teams/${teamId}/roster`);
      const roster = response.data.roster || [];
      console.log('Loaded roster:', roster.length, 'players');
      const defensemen = roster.filter((p: Player) => p.position === 'D');
      console.log('Defensemen in roster:', defensemen.length, defensemen.map((p: Player) => `${p.name} (${p.position})`));
      
      // Always update state with the latest roster from the server
      if (Array.isArray(roster)) {
        console.log('Setting roster state with', roster.length, 'players');
        const defensemenCount = roster.filter((p: Player) => p.position === 'D').length;
        console.log('Defensemen count in new roster:', defensemenCount);
        setUserRoster([...roster]); // Create new array to ensure React detects the change
      } else {
        console.error('Invalid roster data received:', roster);
      }
      
      // Load line assignments
      try {
        const linesResponse = await api.get(`/api/teams/${teamId}/lines`);
        const existingLines = linesResponse.data.lines || [];
        setUserLines(existingLines);
        
        // If no lines exist, check if draft is complete and auto-populate
        if (existingLines.length === 0) {
          const simResponse = await api.get(`/api/simulations/${simulationId}`);
          if (simResponse.data.simulation.status !== 'draft') {
            // Draft is complete but lines aren't populated, try to auto-populate
            try {
              await api.post(`/api/teams/${teamId}/lines`);
              // Reload lines after auto-population
              const updatedLinesResponse = await api.get(`/api/teams/${teamId}/lines`);
              setUserLines(updatedLinesResponse.data.lines || []);
            } catch (autoPopError) {
              console.error('Failed to auto-populate lines', autoPopError);
            }
          }
        }
      } catch (linesError) {
        console.error('Failed to load line assignments', linesError);
        setUserLines([]);
      }
      
      // Load team to get coach
      const teamResponse = await api.get(`/api/teams/${teamId}`);
      if (teamResponse.data.team.coach_id) {
        // Load coach details
        const coachesResponse = await api.get('/api/players/coaches');
        const coach = coachesResponse.data.coaches.find((c: any) => c.id === teamResponse.data.team.coach_id);
        setUserCoach(coach || null);
      } else {
        setUserCoach(null);
      }
    } catch (error) {
      console.error('Failed to load user roster', error);
      // Retry once if it fails
      if (retryCount < 1) {
        await new Promise(resolve => setTimeout(resolve, 500));
        return loadUserRoster(teamId, retryCount + 1);
      }
    }
  };

  const updateCurrentPick = async (skipRosterReload: boolean = false) => {
    try {
      const pickResponse = await api.get(`/api/simulations/${simulationId}/draft/current`);
      if (pickResponse.data.draft_complete) {
        // Reload roster and lines before redirecting to show populated lines
        if (userTeam) {
          await loadUserRoster(userTeam.id);
          // Small delay to ensure lines are visible
          await new Promise(resolve => setTimeout(resolve, 500));
        }
        router.push(`/simulation/${simulationId}`);
        return;
      }
      setCurrentPick(pickResponse.data);
      setIsCoachesRound(pickResponse.data.round === 21);
      
      // Reload available players and coaches (remove drafted ones)
      await refreshAvailableEntities();
      
      // Reload draft history
      await loadDraftHistory();
      
      // Only reload user roster if not skipped (to avoid race conditions after making a pick)
      // We skip reload when we just made a pick because makePick already reloaded it
      if (!skipRosterReload && userTeam) {
        // Small delay to ensure any backend operations are complete
        await new Promise(resolve => setTimeout(resolve, 100));
        await loadUserRoster(userTeam.id);
      }
    } catch (error) {
      console.error('Failed to update current pick', error);
    }
  };

  const refreshAvailableEntities = async () => {
    try {
      // Use draft history to get all drafted players/coaches - more reliable
      const historyResponse = await api.get(
        `/api/simulations/${simulationId}/draft/history?t=${Date.now()}`
      );
      const history = historyResponse.data.history || [];
      
      const draftedPlayerIds = new Set<number>();
      const draftedCoachIds = new Set<number>();

      // Get all drafted players and coaches from history
      history.forEach((pick: any) => {
        if (pick.player) {
          draftedPlayerIds.add(pick.player.id);
        }
        if (pick.coach) {
          draftedCoachIds.add(pick.coach.id);
        }
      });

      // Also check all teams' current rosters and coaches
      const allTeams = teams.map((t: Team) => t.id);
      for (const teamId of allTeams) {
        try {
          const rosterResponse = await api.get(`/api/teams/${teamId}/roster`);
          (rosterResponse.data.roster || []).forEach((p: Player) => {
            draftedPlayerIds.add(p.id);
          });

          const teamResponse = await api.get(`/api/teams/${teamId}`);
          if (teamResponse.data.team.coach_id) {
            draftedCoachIds.add(teamResponse.data.team.coach_id);
          }
        } catch (err) {
          // Team might not have roster yet
        }
      }

      // Load all players and filter
      const playersResponse = await api.get('/api/players/');
      const allPlayers = playersResponse.data.players || [];
      setAvailablePlayers(allPlayers.filter((p: Player) => !draftedPlayerIds.has(p.id)));

      // Load coaches and filter
      const coachesResponse = await api.get('/api/players/coaches');
      const allCoaches = coachesResponse.data.coaches || [];
      setAvailableCoaches(allCoaches.filter((c: any) => !draftedCoachIds.has(c.id)));
    } catch (error) {
      console.error('Failed to refresh available entities', error);
    }
  };

  const makePick = async (playerId?: number, coachId?: number) => {
    try {
      // Clear timer interval to prevent multiple calls
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }

      const response = await api.post(`/api/simulations/${simulationId}/draft`, {
        player_id: playerId,
        coach_id: coachId
      });

      if (response.data.draft_complete) {
        router.push(`/simulation/${simulationId}`);
      } else {
        // Wait a bit to ensure backend has committed the transaction
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Reload user roster after making a pick (always reload to get latest roster)
        if (userTeam) {
          console.log('Making pick - reloading roster for team', userTeam.id);
          await loadUserRoster(userTeam.id);
          // Wait a bit more and reload again to ensure we have the committed data
          await new Promise(resolve => setTimeout(resolve, 300));
          await loadUserRoster(userTeam.id);
          // One more reload after a delay to be absolutely sure
          await new Promise(resolve => setTimeout(resolve, 200));
          await loadUserRoster(userTeam.id);
        }
        
        // Update current pick (skip roster reload to avoid overwriting)
        await updateCurrentPick(true);
        
        // Reload draft history
        await loadDraftHistory();
        
        // Final roster check after everything
        if (userTeam) {
          await new Promise(resolve => setTimeout(resolve, 100));
          await loadUserRoster(userTeam.id);
        }
      }
    } catch (error: any) {
      console.error('Failed to make pick', error);
      const errorMsg =
        error?.response?.data?.error ||
        error?.message ||
        'Failed to make pick';
      if (!playerId && !coachId) {
        // Silent fail for auto-pick, just log it
        console.error('Auto-pick failed');
      } else {
        await showAlert(errorMsg);
      }
      setIsAutoPicking(false);
    }
  };

  // Update audio volume when mute state changes
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : 1;
    }
  }, [isMuted]);

  const handleSimToNext = async () => {
    try {
      const response = await api.post(`/api/simulations/${simulationId}/draft/sim-to-next`);
      if (response.data.error) {
        await showAlert(`Sim failed: ${response.data.error}`);
        return;
      }
      if (response.data.draft_complete) {
        router.push(`/simulation/${simulationId}`);
      } else {
        // Reload user roster if it became our turn
        if (response.data.next_pick?.is_user_team && userTeam) {
          await loadUserRoster(userTeam.id);
          await updateCurrentPick(true); // Skip roster reload since we just did it
        } else {
          await updateCurrentPick();
        }
        await loadDraftHistory();
      }
    } catch (error) {
      console.error('Failed to sim to next pick', error);
    }
  };

  const handleSimNextAI = async () => {
    // Prevent multiple simultaneous calls
    if (isProcessingAIPickRef.current) {
      console.log('AI pick already in progress, skipping...');
      return;
    }
    
    isProcessingAIPickRef.current = true;
    
    try {
      const response = await api.post(`/api/simulations/${simulationId}/draft/sim-next-ai`);
      if (response.data.error) {
        console.error('AI pick error:', response.data.error);
        await showAlert(`AI pick failed: ${response.data.error}`);
        // Still refresh to see current state
        await updateCurrentPick();
        await loadDraftHistory();
        return;
      }
      
      // Check debug info
      if (response.data.debug) {
        console.log('AI Pick Debug:', response.data.debug);
        if (response.data.warning) {
          console.warn('AI Pick Warning:', response.data.warning);
        }
        if (!response.data.debug.roster_added) {
          console.error('CRITICAL: AI pick did not add a roster entry!', response.data);
        }
      }
      if (response.data.draft_complete) {
        router.push(`/simulation/${simulationId}`);
      } else {
        // Small delay to ensure backend transaction is fully committed
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Reload user roster if it became our turn
        if (response.data.next_pick?.is_user_team && userTeam) {
          await loadUserRoster(userTeam.id);
          await updateCurrentPick(true); // Skip roster reload since we just did it
        } else {
          await updateCurrentPick();
        }
        
        // Small delay before loading history to ensure data is available
        await new Promise(resolve => setTimeout(resolve, 50));
        await loadDraftHistory();
      }
    } catch (error: any) {
      console.error('Failed to sim next AI pick', error);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to simulate AI pick';
      await showAlert(`Error: ${errorMsg}`);
      // Refresh to see current state
      await updateCurrentPick();
      await loadDraftHistory();
    } finally {
      // Always reset the flag, even if there was an error
      isProcessingAIPickRef.current = false;
    }
  };

  const handleSimAll = async () => {
    const confirmed = await showConfirm('Simulate entire draft? This will auto-pick all remaining selections.');
    if (!confirmed) {
      return;
    }
    try {
      const response = await api.post(`/api/simulations/${simulationId}/draft/sim-all`);
      if (response.data.draft_complete) {
        router.push(`/simulation/${simulationId}`);
      } else {
        await updateCurrentPick();
      }
    } catch (error) {
      console.error('Failed to sim all draft', error);
    }
  };

  // Separate players into skaters and goalies
  const skaters = availablePlayers.filter(p => !p.is_goalie && p.position !== 'G');
  const goalies = availablePlayers.filter(p => p.is_goalie || p.position === 'G');

  const filteredSkaters = skaters
    .filter(p => {
      if (filter === 'all') return true;
      if (filter === 'skaters') return true; // Show all skaters
      if (filter === 'D') return p.position === 'LD' || p.position === 'RD'; // Show both LD and RD
      if (filter === 'LD') return p.position === 'LD';
      if (filter === 'RD') return p.position === 'RD';
      return p.position === filter; // For C, LW, RW
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'overall') {
        const aOverall = a.overall || 0;
        const bOverall = b.overall || 0;
        return bOverall - aOverall;
      }
      return (b as any)[sortBy] - (a as any)[sortBy];
    });

  const filteredGoalies = goalies.sort((a, b) => {
    if (sortBy === 'name') return a.name.localeCompare(b.name);
    const aOverall = a.overall || 0;
    const bOverall = b.overall || 0;
    return bOverall - aOverall;
  });

  const filteredCoaches = availableCoaches.sort((a, b) => b.rating - a.rating);

  const getPositionCounts = () => {
    const counts: { [key: string]: number } = { C: 0, LW: 0, RW: 0, D: 0, G: 0 };
    userRoster.forEach(p => {
      // Handle defensive positions (LD, RD) as D
      if (p.position === 'LD' || p.position === 'RD') {
        counts.D++;
      } else if (counts.hasOwnProperty(p.position)) {
        counts[p.position]++;
      } else {
        // Log unexpected positions (only if not LD/RD which we already handled)
        console.warn('Unexpected position in roster:', p.name, p.position);
      }
    });
    return counts;
  };

  const positionCounts = getPositionCounts();

  // Format team name to remove abbreviation repetition
  const formatTeamName = (teamName: string) => {
    // Remove abbreviation if it appears at the end (e.g., "Los Angeles LA" -> "Los Angeles")
    return teamName.replace(/\s+\w+$/, '');
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <p className="text-dark-text-muted">Loading draft...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Lottery Modal */}
      {showLotteryModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-dark-surface border border-dark-border rounded-lg p-6 max-w-2xl w-full relative">
            <button
              onClick={() => {
                setIsMuted(!isMuted);
                if (audioRef.current) {
                  audioRef.current.volume = !isMuted ? 0 : 1;
                }
              }}
              className="absolute top-4 right-4 p-2 hover:bg-dark-card rounded-lg transition-colors"
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? (
                <svg className="w-6 h-6 text-dark-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-dark-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              )}
            </button>
            <h2 className="text-2xl font-bold text-center mb-3 text-primary-400">Draft Lottery</h2>
            <p className="text-center text-dark-text-muted mb-3 text-sm">First Round Draft Order</p>
            {lotteryRevealed < lotteryOrder.length && (
              <>
                <p className="text-center text-primary-400 font-semibold mb-3 text-sm">
                  Next reveal in: {lotteryTimer}s
                </p>
                <div className="flex justify-center mb-4">
                  <button
                    onClick={skipLotteryAnimation}
                    className="btn btn-secondary btn-sm"
                  >
                    Skip Animation
                  </button>
                </div>
              </>
            )}
            <div className={lotteryOrder.length >= 10 ? "grid grid-cols-2 gap-2" : "space-y-2"}>
              {[...lotteryOrder].reverse().map((team, reverseDisplayIndex) => {
                // Show in reverse order (last team first, first team last)
                // Reveal from last to first: if lotteryRevealed is N, show last N teams
                // reverseDisplayIndex 0 = last team, reverseDisplayIndex N-1 = first team
                const originalIndex = lotteryOrder.length - 1 - reverseDisplayIndex;
                // If lotteryRevealed = 1, show reverseDisplayIndex 0 (last team)
                // If lotteryRevealed = 2, show reverseDisplayIndex 0,1 (last 2 teams)
                const isRevealed = reverseDisplayIndex < lotteryRevealed;
                
                return (
                  <div
                    key={team.team_id}
                    className={`p-2 rounded-lg border transition-all duration-500 ${
                      isRevealed
                        ? 'bg-primary-500/20 border-primary-500/50 text-dark-text opacity-100'
                        : 'bg-dark-surface border-dark-border text-dark-text-muted opacity-30'
                    }`}
                    style={{
                      transitionDelay: isRevealed ? '0ms' : undefined
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-base font-bold ${isRevealed ? 'text-dark-text' : 'text-dark-text-muted'}`}>
                        #{originalIndex + 1}
                      </span>
                      {isRevealed ? (
                        <span className="text-sm font-semibold text-dark-text">{formatTeamName(team.team_name)}</span>
                      ) : (
                        <span className="text-sm font-semibold text-transparent select-none" aria-hidden="true">
                          ••••••••••
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            {lotteryRevealed < lotteryOrder.length && (
              <p className="text-center text-dark-text-muted mt-6">
                Revealing draft order...
              </p>
            )}
          </div>
        </div>
      )}
      <div className="max-w-7xl mx-auto">
        {/* Header with Timer and Controls */}
        <div className="card mb-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-dark-text">Draft</h1>
            {currentPick && (
              <div className="flex items-center gap-4">
                <div className={`text-2xl font-bold ${timer < 10 ? 'text-red-400' : timer < 30 ? 'text-orange-400' : 'text-dark-text'}`}>
                  {formatTime(timer)}
                </div>
                <div className="text-sm text-dark-text-muted">
                  {currentPick.is_user_team ? 'Your Pick' : 'AI Pick'}
                </div>
              </div>
            )}
          </div>
          
          {currentPick && (
            <>
              <div className="bg-primary-500/10 border border-primary-500/30 p-4 rounded-lg mb-4">
                <p className="text-lg text-dark-text">
                  <span className="font-bold">Round {currentPick.round}</span> - Pick {currentPick.pick}/{currentPick.total_picks}
                </p>
                <p className="text-xl font-bold text-primary-400">
                  {currentPick.team_name.replace(/\s+\w+$/, '')} is picking...
                </p>
              </div>

              {/* Recent Picks - Horizontal Scrollable */}
              {draftHistory.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-semibold mb-2 text-dark-text">Recent Picks</h4>
                  <div 
                    className="overflow-x-auto overflow-y-hidden pb-2" 
                    style={{ 
                      // Constrain to exactly 5 cards width: 5 * 200px + 4 * 12px (gap) = 1048px
                      // Use max-width to prevent expansion, but allow smaller on mobile
                      width: '100%',
                      maxWidth: '1048px',
                      maxHeight: '120px',
                      boxSizing: 'border-box'
                    }}
                  >
                    <div className="flex gap-3" style={{ width: 'max-content' }}>
                      {draftHistory.slice(-5).reverse().map((pick: any) => (
                        <div
                          key={pick.pick}
                          className={`flex-shrink-0 p-3 rounded-lg border ${
                            pick.is_user_team
                              ? 'bg-primary-500/10 border-primary-500/30'
                              : 'bg-dark-surface border-dark-border'
                          }`}
                          style={{ 
                            width: '200px', 
                            minWidth: '200px', 
                            maxWidth: '200px',
                            flexShrink: 0
                          }}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs text-dark-text-muted">
                              R{pick.round} - P{pick.pick}
                            </span>
                            <span className={`text-xs font-semibold ${pick.is_user_team ? 'text-primary-400' : 'text-dark-text'}`}>
                              {formatTeamName(pick.team_name)}
                            </span>
                          </div>
                          {pick.player ? (
                            <div className="text-sm text-dark-text">
                              <div className="font-medium">{pick.player.name}</div>
                              <div className="text-xs text-dark-text-muted">
                                {pick.player.position} - <span className="text-orange-400 font-semibold">OVR: {pick.player.overall?.toFixed(1)}</span>
                              </div>
                            </div>
                          ) : pick.coach ? (
                            <div className="text-sm text-dark-text">
                              <div className="font-medium">{pick.coach.name}</div>
                              <div className="text-xs text-dark-text-muted">
                                Coach - <span className="text-orange-400 font-semibold">Rating: {pick.coach.rating}</span>
                              </div>
                            </div>
                          ) : (
                            <div className="text-sm text-dark-text-muted/50 italic">
                              Empty pick
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Simulation Controls */}
          <div className="flex gap-2 flex-wrap">
            {currentPick && !currentPick.is_user_team && (
              <>
                <button
                  onClick={handleSimNextAI}
                  className="btn btn-secondary btn-sm"
                >
                  Sim Next AI Pick
                </button>
                <button
                  onClick={handleSimToNext}
                  className="btn btn-secondary btn-sm"
                >
                  Sim to My Next Pick
                </button>
              </>
            )}
            <button
              onClick={handleSimAll}
              className="btn btn-secondary btn-sm"
            >
              Sim All Draft
            </button>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4">
          {/* Available Players/Coaches */}
          <div className="col-span-8 card">
            <h2 className="text-xl font-bold mb-4 text-dark-text">
              {isCoachesRound ? 'Available Coaches' : 'Available Players'}
            </h2>
            
            <>
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-dark-text-muted mb-2">
                    Filter
                  </label>
                  <select
                    className="input w-full"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                  >
                    <option value="all">All Players</option>
                    <option value="skaters">Skaters Only</option>
                    <option value="goalies">Goalies Only</option>
                    <option value="coaches">Coaches</option>
                    <optgroup label="Forwards">
                      <option value="C">Centers</option>
                      <option value="LW">Left Wing</option>
                      <option value="RW">Right Wing</option>
                    </optgroup>
                    <optgroup label="Defense">
                      <option value="D">All Defense</option>
                      <option value="LD">Left Defense</option>
                      <option value="RD">Right Defense</option>
                    </optgroup>
                  </select>
                </div>

                <div className="flex-1">
                  <label className="block text-sm font-medium text-dark-text-muted mb-2">
                    Sort By
                  </label>
                  <select
                    className="input w-full"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                  >
                    <option value="overall">Overall</option>
                    <option value="off">Offense</option>
                    <option value="def">Defense</option>
                    <option value="phys">Physical</option>
                    <option value="name">Name</option>
                  </select>
                </div>
              </div>

              {/* Skaters Table */}
              {(filter === 'all' || filter === 'skaters' || filter === 'C' || filter === 'LW' || filter === 'RW' || filter === 'D' || filter === 'LD' || filter === 'RD') && filteredSkaters.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-2 text-dark-text">Skaters</h3>
                  <div className="overflow-auto max-h-96">
                    <table className="w-full text-sm">
                      <thead className="bg-dark-surface sticky top-0">
                        <tr>
                          <th className="p-2 text-left text-dark-text text-xs">Player</th>
                          <th className="p-2 text-center text-dark-text text-xs">Pos</th>
                          <th className="p-2 text-center text-dark-text text-xs">Type</th>
                          <th className="p-2 text-center text-dark-text text-xs">Era</th>
                          <th className="p-2 text-center text-dark-text text-xs">OVR</th>
                          <th className="p-2 text-center text-dark-text text-xs">OFF</th>
                          <th className="p-2 text-center text-dark-text text-xs">DEF</th>
                          <th className="p-2 text-center text-dark-text text-xs">PHYS</th>
                          <th className="p-2 text-center text-dark-text text-xs">LEAD</th>
                          <th className="p-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredSkaters.map(player => (
                          <tr key={player.id} className="border-b border-dark-border hover:bg-dark-surface">
                            <td className="p-2 font-medium text-dark-text text-xs">{player.name}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.position}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.player_type || '-'}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.era || '-'}</td>
                            <td className="p-2 text-center font-bold text-orange-400 text-xs">{player.overall?.toFixed(1) || 'N/A'}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.off}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.def}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.phys}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.lead}</td>
                            <td className="p-2">
                              {currentPick?.is_user_team && (
                                <button
                                  onClick={() => makePick(player.id)}
                                  className="btn btn-primary btn-sm text-xs px-2 py-1"
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
              )}

              {/* Goalies Table */}
              {(filter === 'all' || filter === 'goalies') && filteredGoalies.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-2 text-dark-text">Goalies</h3>
                  <div className="overflow-auto max-h-96">
                    <table className="w-full text-sm">
                      <thead className="bg-dark-surface sticky top-0">
                        <tr>
                          <th className="p-2 text-left text-dark-text text-xs">Goalie</th>
                          <th className="p-2 text-center text-dark-text text-xs">Era</th>
                          <th className="p-2 text-center text-dark-text text-xs">OVR</th>
                          <th className="p-2 text-center text-dark-text text-xs">CONST</th>
                          <th className="p-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredGoalies.map(player => (
                          <tr key={player.id} className="border-b border-dark-border hover:bg-dark-surface">
                            <td className="p-2 font-medium text-dark-text text-xs">{player.name}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.era || '-'}</td>
                            <td className="p-2 text-center font-bold text-orange-400 text-xs">{player.overall?.toFixed(1) || 'N/A'}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{player.const}</td>
                            <td className="p-2">
                              {currentPick?.is_user_team && (
                                <button
                                  onClick={() => makePick(player.id)}
                                  className="btn btn-primary btn-sm text-xs px-2 py-1"
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
              )}

              {/* Coaches Table - Always visible below goalies */}
              {(filter === 'all' || filter === 'coaches') && filteredCoaches.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2 text-dark-text">Coaches</h3>
                  <div className="overflow-auto max-h-96">
                    <table className="w-full text-sm">
                      <thead className="bg-dark-surface sticky top-0">
                        <tr>
                          <th className="p-2 text-left text-dark-text text-xs">Coach</th>
                          <th className="p-2 text-center text-dark-text text-xs">Type</th>
                          <th className="p-2 text-center text-dark-text text-xs">Era</th>
                          <th className="p-2 text-center text-dark-text text-xs">Rating</th>
                          <th className="p-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredCoaches.map(coach => (
                          <tr key={coach.id} className="border-b border-dark-border hover:bg-dark-surface">
                            <td className="p-2 font-medium text-dark-text text-xs">{coach.name}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{coach.coach_type || '-'}</td>
                            <td className="p-2 text-center text-dark-text text-xs">{coach.era || '-'}</td>
                            <td className="p-2 text-center font-bold text-orange-400 text-xs">{coach.rating}</td>
                            <td className="p-2">
                              {currentPick?.is_user_team && (
                                <button
                                  onClick={() => makePick(undefined, coach.id)}
                                  className="btn btn-primary btn-sm text-xs px-2 py-1"
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
              )}
            </>
          </div>

          {/* Sidebar: Team Roster & Draft Board */}
          <div className="col-span-4 space-y-4">
            {/* User Team Lineup */}
            {userTeam && (
              <div className="card">
                <h3 className="font-bold mb-2 text-lg text-dark-text">{userTeam.city} {userTeam.name} - Your Team</h3>
                
                <div className="mb-4">
                  <h4 className="font-semibold mb-2 text-dark-text">Position Counts</h4>
                  <div className="grid grid-cols-5 gap-2 text-sm">
                    <div className="text-dark-text">C: {positionCounts.C}/4</div>
                    <div className="text-dark-text">LW: {positionCounts.LW}/4</div>
                    <div className="text-dark-text">RW: {positionCounts.RW}/4</div>
                    <div className="text-dark-text">D: {positionCounts.D}/6</div>
                    <div className="text-dark-text">G: {positionCounts.G}/2</div>
                  </div>
                </div>

                <div className="mb-4">
                  <h4 className="font-semibold mb-2 text-dark-text">Forward Lines</h4>
                  {[1, 2, 3, 4].map(lineNum => {
                    // Get players from line assignments if available, otherwise fallback to roster order
                    let lw, c, rw;
                    
                    if (userLines.length > 0) {
                      // Use line assignments
                      const lwLine = userLines.find((l: any) => l.line_type === 'forward' && l.line_number === lineNum && l.position === 'LW');
                      const cLine = userLines.find((l: any) => l.line_type === 'forward' && l.line_number === lineNum && l.position === 'C');
                      const rwLine = userLines.find((l: any) => l.line_type === 'forward' && l.line_number === lineNum && l.position === 'RW');
                      
                      lw = lwLine ? userRoster.find((p: Player) => p.id === lwLine.player_id) : null;
                      c = cLine ? userRoster.find((p: Player) => p.id === cLine.player_id) : null;
                      rw = rwLine ? userRoster.find((p: Player) => p.id === rwLine.player_id) : null;
                    } else {
                      // Fallback to roster order
                      lw = userRoster.filter(p => p.position === 'LW')[(lineNum - 1)];
                      c = userRoster.filter(p => p.position === 'C')[(lineNum - 1)];
                      rw = userRoster.filter(p => p.position === 'RW')[(lineNum - 1)];
                    }
                    
                    return (
                      <div key={lineNum} className="mb-2 p-2 bg-dark-surface rounded text-sm">
                        <div className="font-medium mb-1 text-dark-text">Line {lineNum}</div>
                        {lw || c || rw ? (
                          <div className="space-y-1">
                            {lw ? (
                              <div className="text-dark-text-muted">
                                LW - {lw.name} <span className="text-dark-text">(OVR: {lw.overall?.toFixed(1)})</span>
                              </div>
                            ) : (
                              <div className="text-dark-text-muted/50">LW - Empty</div>
                            )}
                            {c ? (
                              <div className="text-dark-text-muted">
                                C - {c.name} <span className="text-dark-text">(OVR: {c.overall?.toFixed(1)})</span>
                              </div>
                            ) : (
                              <div className="text-dark-text-muted/50">C - Empty</div>
                            )}
                            {rw ? (
                              <div className="text-dark-text-muted">
                                RW - {rw.name} <span className="text-dark-text">(OVR: {rw.overall?.toFixed(1)})</span>
                              </div>
                            ) : (
                              <div className="text-dark-text-muted/50">RW - Empty</div>
                            )}
                          </div>
                        ) : (
                          <div className="text-dark-text-muted/50">Empty</div>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="mb-4">
                  <h4 className="font-semibold mb-2 text-dark-text">Defense Pairs</h4>
                  {[1, 2, 3].map(pairNum => {
                    // Get players from line assignments if available, otherwise fallback to roster order
                    let ld, rd;
                    
                    if (userLines.length > 0) {
                      // Use line assignments
                      const ldLine = userLines.find((l: any) => l.line_type === 'defense' && l.line_number === pairNum && l.position === 'LD');
                      const rdLine = userLines.find((l: any) => l.line_type === 'defense' && l.line_number === pairNum && l.position === 'RD');
                      
                      ld = ldLine ? userRoster.find((p: Player) => p.id === ldLine.player_id) : null;
                      rd = rdLine ? userRoster.find((p: Player) => p.id === rdLine.player_id) : null;
                    } else {
                      // Fallback to roster order - separate LD and RD
                      const leftDefensemen = userRoster.filter(p => p.position === 'LD');
                      const rightDefensemen = userRoster.filter(p => p.position === 'RD');
                      ld = leftDefensemen[pairNum - 1] || null;
                      rd = rightDefensemen[pairNum - 1] || null;
                    }
                    
                    return (
                      <div key={pairNum} className="mb-2 p-2 bg-dark-surface rounded text-sm">
                        <div className="font-medium mb-1 text-dark-text">Pair {pairNum}</div>
                        {ld || rd ? (
                          <div className="space-y-1">
                            {ld ? (
                              <div className="text-dark-text-muted">
                                LD - {ld.name} <span className="text-dark-text">(OVR: {ld.overall?.toFixed(1)})</span>
                              </div>
                            ) : (
                              <div className="text-dark-text-muted/50">LD - Empty</div>
                            )}
                            {rd ? (
                              <div className="text-dark-text-muted">
                                RD - {rd.name} <span className="text-dark-text">(OVR: {rd.overall?.toFixed(1)})</span>
                              </div>
                            ) : (
                              <div className="text-dark-text-muted/50">RD - Empty</div>
                            )}
                          </div>
                        ) : (
                          <div className="text-dark-text-muted/50">Empty</div>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="mb-4">
                  <h4 className="font-semibold mb-2 text-dark-text">Goalies</h4>
                  {(() => {
                    let goalies: Player[] = [];
                    
                    if (userLines.length > 0) {
                      // Use line assignments
                      const goalieLines = userLines
                        .filter((l: any) => l.line_type === 'goalie')
                        .sort((a: any, b: any) => a.line_number - b.line_number);
                      
                      goalies = goalieLines
                        .map((l: any) => userRoster.find((p: Player) => p.id === l.player_id))
                        .filter((p: Player | undefined): p is Player => p !== undefined);
                    } else {
                      // Fallback to roster order
                      goalies = userRoster.filter(p => p.position === 'G' || p.is_goalie);
                    }
                    
                    return goalies.length > 0 ? (
                      <div className="space-y-2">
                        {goalies.slice(0, 2).map((p, idx) => (
                          <div key={p.id} className="mb-2 p-2 bg-dark-surface rounded text-sm">
                            <div className="font-medium mb-1 text-dark-text">G{idx + 1}</div>
                            <div className="text-dark-text-muted">
                              {p.name} <span className="text-dark-text">(OVR: {p.overall?.toFixed(1)})</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-dark-text-muted/50 text-sm p-2 bg-dark-surface rounded">No goalies drafted</div>
                    );
                  })()}
                </div>

                {/* Coach Section - Same style as Forward Lines and Goalies */}
                <div>
                  <h4 className="font-semibold mb-2 text-dark-text">Coach</h4>
                  {userCoach ? (
                    <div className="mb-2 p-2 bg-dark-surface rounded text-sm">
                      <div className="font-medium mb-1 text-dark-text">Coach</div>
                      <div className="text-dark-text-muted">
                        {userCoach.name} <span className="text-dark-text">(Rating: {userCoach.rating})</span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-dark-text-muted/50 text-sm p-2 bg-dark-surface rounded">No coach selected</div>
                  )}
                </div>
              </div>
            )}

            {/* Draft Board */}
            <div className="card">
              <h3 className="font-bold mb-2 text-dark-text">Draft Order</h3>
              <div className="space-y-2 max-h-64 overflow-auto">
                {teams.map(team => (
                  <div 
                    key={team.id} 
                    className={`p-2 rounded text-sm ${
                      team.user_controlled 
                        ? 'bg-primary-500/20 font-bold border border-primary-500/30 text-primary-400' 
                        : currentPick?.team_id === team.id
                        ? 'bg-yellow-500/20 border border-yellow-500/30 text-dark-text'
                        : 'bg-dark-surface border border-dark-border text-dark-text'
                    }`}
                  >
                    {formatTeamName(`${team.city} ${team.name}`)}
                    {team.user_controlled && ' (You)'}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}