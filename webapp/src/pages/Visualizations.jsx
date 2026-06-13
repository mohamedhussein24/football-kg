import { useState, useEffect } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import './Visualizations.css'

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b', '#fa709a']

function Visualizations() {
  const [playerStats, setPlayerStats] = useState([])
  const [teamComparison, setTeamComparison] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Comparison State
  const [comparisonMode, setComparisonMode] = useState('players') // 'players' or 'teams'
  const [selectedPlayers, setSelectedPlayers] = useState([])
  const [selectedTeams, setSelectedTeams] = useState([])
  const [selectedMetrics, setSelectedMetrics] = useState({
    goals: true,
    assists: true,
    rating: true, // For players
    avgGoals: false, // For teams
    playerCount: false // For teams
  })

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch stats independently so one failure doesn't block the other
      try {
        const statsRes = await axios.get('/api/players/stats')
        setPlayerStats(statsRes.data)
        // Select top 3 players by default for comparison
        if (statsRes.data.length > 0) {
          setSelectedPlayers(statsRes.data.slice(0, 3).map(p => p.playerLabel))
        }
      } catch (e) {
        console.error("Failed to fetch player stats", e)
      }

      try {
        const teamsRes = await axios.get('/api/teams/comparison')
        setTeamComparison(teamsRes.data)
        // Select top 3 teams by default
        if (teamsRes.data.length > 0) {
          setSelectedTeams(teamsRes.data.slice(0, 3).map(t => t.teamLabel))
        }
      } catch (e) {
        console.error("Failed to fetch team comparison", e)
      }

      setLoading(false)
    } catch (err) {
      setError('Failed to fetch visualization data. Please ensure the backend API is running.')
      setLoading(false)
      console.error('Error fetching data:', err)
    }
  }

  // Handle Selection
  const togglePlayerSelection = (playerLabel) => {
    if (selectedPlayers.includes(playerLabel)) {
      setSelectedPlayers(selectedPlayers.filter(p => p !== playerLabel))
    } else {
      if (selectedPlayers.length < 5) {
        setSelectedPlayers([...selectedPlayers, playerLabel])
      } else {
        alert("Max 5 players for clear comparison")
      }
    }
  }

  const toggleTeamSelection = (teamLabel) => {
    if (selectedTeams.includes(teamLabel)) {
      setSelectedTeams(selectedTeams.filter(t => t !== teamLabel))
    } else {
      if (selectedTeams.length < 5) {
        setSelectedTeams([...selectedTeams, teamLabel])
      } else {
        alert("Max 5 teams for clear comparison")
      }
    }
  }

  const toggleMetric = (metric) => {
    setSelectedMetrics({ ...selectedMetrics, [metric]: !selectedMetrics[metric] })
  }

  // Prepare data for Comparison Charts
  const comparisonData = comparisonMode === 'players'
    ? playerStats.filter(p => selectedPlayers.includes(p.playerLabel)).map(p => ({
      name: p.playerLabel,
      goals: p.totalGoals,
      assists: p.totalAssists,
      rating: p.avgRating
    }))
    : teamComparison.filter(t => selectedTeams.includes(t.teamLabel)).map(t => ({
      name: t.teamLabel,
      goals: t.totalGoals,
      avgGoals: t.avgGoalsPerPlayer,
      playerCount: t.playerCount
    }))

  // Prepare data for Overview Charts
  const topScorersData = playerStats.slice(0, 10).map(p => ({
    name: p.playerLabel.length > 15 ? p.playerLabel.substring(0, 15) + '...' : p.playerLabel,
    fullName: p.playerLabel,
    goals: p.totalGoals,
    assists: p.totalAssists
  }))

  const teamGoalsData = teamComparison.map(t => ({
    name: t.teamLabel.length > 15 ? t.teamLabel.substring(0, 15) + '...' : t.teamLabel,
    fullName: t.teamLabel,
    goals: t.totalGoals,
    players: t.playerCount,
    avgGoals: t.avgGoalsPerPlayer
  }))

  const goalsVsAssistsData = playerStats.slice(0, 8).map(p => ({
    name: p.playerLabel.length > 12 ? p.playerLabel.substring(0, 12) + '...' : p.playerLabel,
    goals: p.totalGoals,
    assists: p.totalAssists
  }))

  return (
    <div className="visualizations">
      <div className="page-header">
        <h1>Data Visualizations</h1>
        <button onClick={fetchData} className="refresh-btn" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh Data'}
        </button>
      </div>

      {/* COMPARISON SECTION */}
      <div className="comparison-section">
        <h2>Interactive Comparison</h2>
        <div className="comparison-controls">
          <div className="mode-toggle">
            <button
              className={`mode-btn ${comparisonMode === 'players' ? 'active' : ''}`}
              onClick={() => setComparisonMode('players')}
            >
              Player Comparison
            </button>
            <button
              className={`mode-btn ${comparisonMode === 'teams' ? 'active' : ''}`}
              onClick={() => setComparisonMode('teams')}
            >
              Team Comparison
            </button>
          </div>

          <div className="selectors-container">
            <div className="entity-selector">
              <h3>Select {comparisonMode === 'players' ? 'Players' : 'Teams'} (Max 5):</h3>
              <div className="scrollable-list">
                {comparisonMode === 'players' ? (
                  playerStats.map(p => (
                    <div key={p.playerLabel} className="checkbox-item">
                      <input
                        type="checkbox"
                        checked={selectedPlayers.includes(p.playerLabel)}
                        onChange={() => togglePlayerSelection(p.playerLabel)}
                        id={`p-${p.playerLabel}`}
                      />
                      <label htmlFor={`p-${p.playerLabel}`}>{p.playerLabel}</label>
                    </div>
                  ))
                ) : (
                  teamComparison.map(t => (
                    <div key={t.teamLabel} className="checkbox-item">
                      <input
                        type="checkbox"
                        checked={selectedTeams.includes(t.teamLabel)}
                        onChange={() => toggleTeamSelection(t.teamLabel)}
                        id={`t-${t.teamLabel}`}
                      />
                      <label htmlFor={`t-${t.teamLabel}`}>{t.teamLabel}</label>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="metrics-selector">
              <h3>Metrics:</h3>
              <div className="metrics-list">
                {comparisonMode === 'players' ? (
                  <>
                    <label><input type="checkbox" checked={selectedMetrics.goals} onChange={() => toggleMetric('goals')} /> Goals</label>
                    <label><input type="checkbox" checked={selectedMetrics.assists} onChange={() => toggleMetric('assists')} /> Assists</label>
                    <label><input type="checkbox" checked={selectedMetrics.rating} onChange={() => toggleMetric('rating')} /> Rating (0-10)</label>
                  </>
                ) : (
                  <>
                    <label><input type="checkbox" checked={selectedMetrics.goals} onChange={() => toggleMetric('goals')} /> Total Goals</label>
                    <label><input type="checkbox" checked={selectedMetrics.avgGoals} onChange={() => toggleMetric('avgGoals')} /> Avg Goals/Player</label>
                    <label><input type="checkbox" checked={selectedMetrics.playerCount} onChange={() => toggleMetric('playerCount')} /> Player Count</label>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="comparison-chart">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {comparisonMode === 'players' ? (
                <>
                  {selectedMetrics.goals && <Bar dataKey="goals" fill="#667eea" name="Goals" />}
                  {selectedMetrics.assists && <Bar dataKey="assists" fill="#764ba2" name="Assists" />}
                  {selectedMetrics.rating && <Bar dataKey="rating" fill="#f093fb" name="Rating" />}
                </>
              ) : (
                <>
                  {selectedMetrics.goals && <Bar dataKey="goals" fill="#4facfe" name="Total Goals" />}
                  {selectedMetrics.avgGoals && <Bar dataKey="avgGoals" fill="#00f2fe" name="Avg Goals/Player" />}
                  {selectedMetrics.playerCount && <Bar dataKey="playerCount" fill="#43e97b" name="Player Count" />}
                </>
              )}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="data-source-info">
        <p>
          <strong>Data Source:</strong> Local Knowledge Graph (football_kg_extended.ttl)
          <br />
          <small>Contains 898 triples of football data including players, teams, matches, and performance metrics</small>
        </p>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading && playerStats.length === 0 ? (
        <div className="loading">Loading visualization data...</div>
      ) : (
        <div className="charts-container">
          {/* Top Scorers Bar Chart */}
          <div className="chart-card">
            <h2>Overview: Top Goal Scorers</h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={topScorersData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip
                  formatter={(value, name) => [value, name === 'goals' ? 'Goals' : 'Assists']}
                  labelFormatter={(label) => topScorersData.find(d => d.name === label)?.fullName || label}
                />
                <Legend />
                <Bar dataKey="goals" fill="#667eea" name="Goals" />
                <Bar dataKey="assists" fill="#764ba2" name="Assists" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Team Goals Comparison */}
          <div className="chart-card">
            <h2>Overview: Team Goals</h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={teamGoalsData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={120} />
                <Tooltip
                  formatter={(value, name) => {
                    if (name === 'goals') return [value, 'Total Goals']
                    if (name === 'players') return [value, 'Players']
                    if (name === 'avgGoals') return [value.toFixed(2), 'Avg Goals/Player']
                    return [value, name]
                  }}
                  labelFormatter={(label) => teamGoalsData.find(d => d.name === label)?.fullName || label}
                />
                <Legend />
                <Bar dataKey="goals" fill="#4facfe" name="Total Goals" />
                <Bar dataKey="avgGoals" fill="#00f2fe" name="Avg Goals/Player" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Goals vs Assists Scatter/Line */}
          <div className="chart-card">
            <h2>Goals vs Assists Performance</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={goalsVsAssistsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="goals" stroke="#667eea" strokeWidth={2} name="Goals" />
                <Line type="monotone" dataKey="assists" stroke="#764ba2" strokeWidth={2} name="Assists" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Top Teams Pie Chart */}
          <div className="chart-card">
            <h2>Top Teams by Total Goals</h2>
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={teamGoalsData.slice(0, 6)}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="goals"
                >
                  {teamGoalsData.slice(0, 6).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [value, 'Total Goals']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}

export default Visualizations

