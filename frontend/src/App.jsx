import React, { useState } from 'react';
import { Plus, Users, Trash2, RefreshCw } from 'lucide-react';

const LoLTeamBalancer = () => {
  const [players, setPlayers] = useState([]);
  const [newPlayer, setNewPlayer] = useState({ username: '', tag: '' });
  const [teams, setTeams] = useState({ team1: [], team2: [] });
  const [isBalancing, setIsBalancing] = useState(false);
  const [expandedPlayer, setExpandedPlayer] = useState(null);
  const [expandedPlayerList, setExpandedPlayerList] = useState(false);
  const [expandedTeam1, setExpandedTeam1] = useState(false);
  const [expandedTeam2, setExpandedTeam2] = useState(false);
  const [isLoadingPlayer, setIsLoadingPlayer] = useState(false);

const API_URL = import.meta.env.VITE_API_URL;
console.log('API URL:', API_URL);

  const roles = ['Top', 'Jungle', 'Middle', 'Bottom', 'Utility'];
  const roleColors = {
    'Top': 'bg-red-100 text-red-800',
    'Jungle': 'bg-green-100 text-green-800', 
    'Middle': 'bg-blue-100 text-blue-800',
    'Bottom': 'bg-purple-100 text-purple-800',
    'Utility': 'bg-yellow-100 text-yellow-800'
  };

  // Helper function to calculate average excluding null/undefined values
  const calculateAverage = (roleScores) => {
    if (!roleScores) return null;
    
    const validScores = Object.values(roleScores).filter(score => score !== null && score !== undefined);
    
    if (validScores.length === 0) return null;
    
    return Math.round(validScores.reduce((a, b) => a + b, 0) / validScores.length);
  };

  // Helper function to display score or N/A
  const displayScore = (score) => {
    return score !== null && score !== undefined ? score : 'N/A';
  };

  // Helper function to calculate team role average (based on assigned roles)
  const calculateTeamRoleAverage = (team) => {
    if (!team || !Array.isArray(team) || team.length === 0) return 0;

    let totalScores = 0;
    let count = 0;

    for (const player of team) {
      if (!player || !player.roleScores || !player.role) continue;

      const roleScore = player.roleScores[player.role];

      // Check that roleScore is a valid number (not null, undefined, "n/a", or NaN)
      if (roleScore !== null && roleScore !== undefined && roleScore !== "n/a" && !isNaN(roleScore)) {
        totalScores += roleScore;
        count += 1;
      }
    }

    return count === 0 ? 0 : Math.round(totalScores / count);
  };


  // Helper function to calculate team overall average (average of each player's overall average)
  const calculateTeamOverallAverage = (team) => {
    if (!team || !Array.isArray(team) || team.length === 0) return 0;
    
    const playerAverages = team.map(player => {
      const playerAvg = calculateAverage(player.roleScores);
      return playerAvg || 0;
    });
    
    const totalAverage = playerAverages.reduce((sum, avg) => sum + avg, 0);
    return Math.round(totalAverage / playerAverages.length);
  };

  const addPlayer = async () => {
    if (!newPlayer.username.trim() || !newPlayer.tag.trim()) return;
  // Check for duplicates
  const exists = players.some(
    p =>
      p.username.toLowerCase() === newPlayer.username.toLowerCase() &&
      p.tag.toLowerCase() === newPlayer.tag.toLowerCase()
  );
  if (exists) {
    alert('Player already added!');
    return;
  }
    setIsLoadingPlayer(true);

    try {
      const response = await fetch(
        `${API_URL}/api/players/${encodeURIComponent(newPlayer.username)}/${encodeURIComponent(newPlayer.tag)}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      // Build roleScores object from aggregates array
      const roleScores = {};
      
      // Initialize all roles as null (no data)
      roles.forEach(role => {
        roleScores[role] = null;
      });

      if (data.aggregates && Array.isArray(data.aggregates)) {
        data.aggregates.forEach(({ role, avg_score }) => {
          // Map API role names to frontend role names
          const roleMapping = {
            'top': 'Top',
            'jungle': 'Jungle',
            'middle': 'Middle', 
            'bottom': 'Bottom',
            'utility': 'Utility'
          };
          const mappedRole = roleMapping[role.toLowerCase()];
          if (mappedRole && avg_score !== null && avg_score !== undefined) {
            roleScores[mappedRole] = Math.round(avg_score);
          }
        });
      }

      const playerData = {
        username: newPlayer.username,
        tag: newPlayer.tag,
        roleScores,
      };

      setPlayers(prev => [...prev, playerData]);
      setNewPlayer({ username: '', tag: '' });
    } catch (error) {
      console.error('Error fetching player data:', error);
      alert(`Failed to add player: ${error.message}`);
    } finally {
    setIsLoadingPlayer(false);
    }
  };

  const removePlayer = (index) => {
    setPlayers(prev => prev.filter((_, i) => i !== index));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoadingPlayer) {
      addPlayer();
    }
  };

  const balanceTeams = async (balanceType = 'role') => {
    if (players.length === 0) {
      alert('Please add some players first');
      return;
    }
    setIsBalancing(true);
    try {
        const result = await fetch(`${API_URL}/api/teams/balance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          balance_type: balanceType,
          summoners: players.map(p => ({
            name: p.username,
            tag: p.tag,
            scores_by_role: {
              top: p.roleScores?.Top || null,
              jungle: p.roleScores?.Jungle || null,
              middle: p.roleScores?.Middle || null,
              bottom: p.roleScores?.Bottom || null,
              utility: p.roleScores?.Utility || null
            }
          }))
        })
      });

      if (!result.ok) {
        const errorText = await result.text();
        throw new Error(`Server error: ${result.status} - ${errorText}`);
      }

      const data = await result.json();
      
      // Map players from response to our player states stored in frontend
      const playerMap = new Map(players.map(p => [`${p.username}#${p.tag}`, p]));
      
      // Safely handle the response data
      const team1Data = Array.isArray(data.team_a) ? data.team_a : [];
      const team2Data = Array.isArray(data.team_b) ? data.team_b : [];
      
      setTeams({
        team1: team1Data.map((playerId, index) => {
          const player = playerMap.get(playerId);
          if (!player) {
            console.warn('Player not found in map:', playerId);
            return null;
          }
          return {
            ...player,
            role: roles[index % roles.length]
          };
        }).filter(Boolean), // Remove any null entries
        team2: team2Data.map((playerId, index) => {
          const player = playerMap.get(playerId);
          if (!player) {
            console.warn('Player not found in map:', playerId);
            return null;
          }
          return {
            ...player,
            role: roles[index % roles.length]
          };
        }).filter(Boolean) // Remove any null entries
      });
    } catch (error) {
      console.error('Error balancing teams:', error);
      alert(`Failed to balance teams: ${error.message}`);
    } finally {
      setIsBalancing(false);
    }
  };


  const PlayerCard = ({ player, index, showRemove = true, isExpanded = false }) => {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-3 transition-all duration-500 ease-in-out">
        <div className="flex justify-between items-start">
          <div className="min-w-0 flex-1">
            <h3 className="font-bold text-gray-900 text-sm truncate">{player.username}</h3>
            <p className="text-xs text-gray-600">#{player.tag}</p>
            {player.role && (
              <div className="mt-2">
                <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${roleColors[player.role]}`}>
                  {player.role}
                </span>
                <span className="ml-2 font-bold text-lg text-gray-900">
                  {displayScore(player.roleScores?.[player.role])}
                </span>
              </div>
            )}
          </div>
          {showRemove && (
            <button
              onClick={() => removePlayer(index)}
              className="text-red-500 hover:text-red-700 p-1 ml-2"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>

        {/* Expanded role scores with smooth height transition */}
        <div className={`transition-all duration-500 ease-in-out overflow-hidden ${
          isExpanded ? 'max-h-32 opacity-100 mt-3' : 'max-h-0 opacity-0 mt-0'
        }`}>
          <div className="pt-3 border-t border-gray-200">
            <div className="text-xs font-medium text-gray-700 mb-2">All Role Scores</div>
            <div className="grid grid-cols-5 gap-1">
              {roles.map(role => (
                <div key={role} className="text-center">
                  <div className={`text-xs px-1 py-1 rounded ${roleColors[role]} mb-1`}>
                    {role === 'Middle' ? 'Mid' : role === 'Bottom' ? 'Bot' : role === 'Utility' ? 'Sup' : role.slice(0, 3)}
                  </div>
                  <div className="text-xs font-medium">
                    {displayScore(player.roleScores?.[role])}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const TeamDisplay = ({ team, teamName, color, isExpanded, setExpanded }) => (
    <div className="mb-8">
      <div className={`bg-white rounded-lg shadow-lg border-t-4 ${color}`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">{teamName}</h2>
            <div className="text-right">
              <div className="mb-2">
                <div className="text-sm text-gray-600">Team Role Average</div>
                <div className="text-xl font-bold text-gray-900">{calculateTeamRoleAverage(team)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Team Overall Average</div>
                <div className="text-xl font-bold text-blue-600">{calculateTeamOverallAverage(team)}</div>
              </div>
            </div>
          </div>
        </div>
        <div 
          className="p-4"
          onMouseEnter={() => setExpanded(true)}
          onMouseLeave={() => setExpanded(false)}
        >
          <div className="grid grid-cols-5 gap-3">
            {team.map((player, index) => (
              <PlayerCard 
                key={`${player.username}-${player.tag}`} 
                player={player} 
                index={index} 
                showRemove={false} 
                isExpanded={isExpanded}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">League of Legends Team Balancer</h1>
          <p className="text-blue-200">Add players and balance them based on their scores. You must have 5 games on a role to recieve a score. Update your dpm.lol profile for recent matches.</p>
        </div>

        {/* Compact Player Management */}
        <div className="bg-white rounded-lg shadow-lg p-4 mb-6">
          <div className="flex items-center gap-4 mb-3">
            <input
              type="text"
              value={newPlayer.username}
              onChange={(e) => setNewPlayer(prev => ({ ...prev, username: e.target.value }))}
              onKeyPress={handleKeyPress}
              disabled={isLoadingPlayer}
              className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="Username"
            />
            <input
              type="text"
              value={newPlayer.tag}
              onChange={(e) => setNewPlayer(prev => ({ ...prev, tag: e.target.value }))}
              onKeyPress={handleKeyPress}
              disabled={isLoadingPlayer}
              className="w-24 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="Tag"
            />
            <button
              onClick={addPlayer}
              disabled={isLoadingPlayer}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm flex items-center gap-1 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isLoadingPlayer ? (
                <RefreshCw size={16} className="animate-spin" />
              ) : (
                <Plus size={16} />
              )}
              {isLoadingPlayer ? 'Loading...' : 'Add'}
            </button>
            <div className="text-sm text-gray-600 font-medium">
              {players.length}/10
            </div>
          </div>
          
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => balanceTeams('role')}
              disabled={isBalancing}
              className="px-4 py-2 rounded text-sm flex items-center gap-1 transition-colors bg-green-600 hover:bg-green-700 text-white disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
            >
              {isBalancing ? (
                <RefreshCw size={16} className="animate-spin" />
              ) : (
                <Users size={16} />
              )}
              {isBalancing ? 'Balancing...' : 'Balance by Role Difference'}
            </button>
            <button
              onClick={() => balanceTeams('role_average')}
              disabled={isBalancing}
              className="px-4 py-2 rounded text-sm flex items-center gap-1 transition-colors bg-purple-600 hover:bg-purple-700 text-white disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
            >
              {isBalancing ? (
                <RefreshCw size={16} className="animate-spin" />
              ) : (
                <Users size={16} />
              )}
              {isBalancing ? 'Balancing...' : 'Balance by Role Average'}
            </button>
            <button
              onClick={() => balanceTeams('overall_average')}
              disabled={isBalancing}
              className="px-4 py-2 rounded text-sm flex items-center gap-1 transition-colors bg-orange-600 hover:bg-orange-700 text-white disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
            >
              {isBalancing ? (
                <RefreshCw size={16} className="animate-spin" />
              ) : (
                <Users size={16} />
              )}
              {isBalancing ? 'Balancing...' : 'Balance by Overall Average'}
            </button>
          </div>
          
          {players.length > 0 && (
            <div 
              className="grid grid-cols-10 gap-1 mt-3"
              onMouseEnter={() => setExpandedPlayerList(true)}
              onMouseLeave={() => setExpandedPlayerList(false)}
            >
              {players.map((player, index) => (
                <div
                  key={index}
                  className="bg-white rounded border border-gray-200 p-1 transition-all duration-500 ease-in-out hover:shadow-md text-center"
                >
                  <div className="mb-1">
                    <div className="font-bold text-xs text-gray-900 truncate" title={player.username}>
                      {player.username.length > 8 ? player.username.slice(0, 8) + '...' : player.username}
                    </div>
                    <div className="text-xs text-gray-600">#{player.tag}</div>
                    <div className="text-sm font-bold text-blue-600 mt-0.5">
                      {displayScore(calculateAverage(player.roleScores))}
                    </div>
                  </div>
                  
                  <div className="flex justify-center">
                    <button
                      onClick={() => removePlayer(index)}
                      className="w-4 h-4 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200 flex items-center justify-center"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Expanded role scores on hover */}
                  <div className={`transition-all duration-500 ease-in-out overflow-hidden ${
                    expandedPlayerList ? 'max-h-24 opacity-100 mt-1' : 'max-h-0 opacity-0 mt-0'
                  }`}>
                    <div className="pt-1 border-t border-gray-200">
                      <div className="space-y-0.5">
                        {roles.map(role => (
                          <div key={role} className="flex justify-between items-center text-xs">
                            <span className={`w-3 h-3 rounded text-xs flex items-center justify-center ${roleColors[role]}`}>
                              {role === 'Middle' ? 'M' : role === 'Bottom' ? 'B' : role === 'Utility' ? 'S' : role.slice(0, 1)}
                            </span>
                            <span className="font-medium">
                              {displayScore(player.roleScores?.[role])}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Balanced Teams */}
        {(teams.team1.length > 0 || teams.team2.length > 0) && (
          <div>
            <TeamDisplay 
              team={teams.team1} 
              teamName="Blue Team" 
              color="border-blue-500" 
              isExpanded={expandedTeam1}
              setExpanded={setExpandedTeam1}
            />
            <TeamDisplay 
              team={teams.team2} 
              teamName="Red Team" 
              color="border-red-500" 
              isExpanded={expandedTeam2}
              setExpanded={setExpandedTeam2}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default LoLTeamBalancer;