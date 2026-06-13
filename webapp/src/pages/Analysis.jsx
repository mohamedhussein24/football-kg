import { useState } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line } from 'recharts'
import './Analysis.css'

function Analysis() {
  const [playerName, setPlayerName] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recommendations, setRecommendations] = useState(null)

  const handleAnalyze = async () => {
    if (!playerName.trim()) {
      setError('Please enter a player name')
      return
    }

    setLoading(true)
    setError(null)
    setAnalysis(null)
    setRecommendations(null)

    try {
      const response = await axios.post('/api/analyze/player', {
        playerName: playerName.trim()
      })

      if (response.data.error) {
        setError(response.data.error)
        setLoading(false)
        return
      }

      setAnalysis(response.data.analysis)
      setRecommendations(response.data.recommendations)
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to analyze player. Please ensure the backend API is running.')
      setLoading(false)
    }
  }

  const prepareRadarData = (stats) => {
    if (!stats) return []
    return [
      {
        subject: 'Goals',
        value: Math.min((stats.totalGoals / 50) * 100, 100),
        fullMark: 100
      },
      {
        subject: 'Assists',
        value: Math.min((stats.totalAssists / 30) * 100, 100),
        fullMark: 100
      },
      {
        subject: 'Consistency',
        value: stats.consistency || 0,
        fullMark: 100
      },
      {
        subject: 'Team Impact',
        value: stats.teamImpact || 0,
        fullMark: 100
      },
      {
        subject: 'Performance',
        value: stats.avgRating || 0,
        fullMark: 100
      }
    ]
  }

  const prepareComparisonData = (player, similar) => {
    if (!similar || similar.length === 0) return []

    return [
      {
        name: player?.playerLabel || 'Player',
        goals: player?.totalGoals || 0,
        assists: player?.totalAssists || 0,
        rating: player?.avgRating || 0
      },
      ...similar.slice(0, 3).map(p => ({
        name: p.playerLabel,
        goals: p.totalGoals || 0,
        assists: p.totalAssists || 0,
        rating: p.avgRating || 0
      }))
    ]
  }

  return (
    <div className="analysis-page">
      <div className="page-header">
        <h1>Player Analysis & Recommendations</h1>
        <p className="subtitle">Comprehensive analysis combining local knowledge graph and external data sources</p>
      </div>

      <div className="search-section">
        <div className="search-box">
          <input
            type="text"
            placeholder="Enter player name (e.g., 'Ronaldo', 'Messi', 'Haaland')"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
            className="player-input"
          />
          <button onClick={handleAnalyze} className="analyze-btn" disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze Player'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {analysis && (
        <div className="analysis-results">
          {/* Player Overview */}
          <div className="analysis-card overview-card">
            <h2>Player Overview</h2>
            <div className="overview-content">
              <div className="overview-header">
                <img
                  src={analysis.thumb || analysis.cutout || 'https://via.placeholder.com/150'}
                  alt={analysis.realName || analysis.playerLabel}
                  className="player-photo"
                />
                <div className="player-title">
                  <h3>{analysis.realName || analysis.playerLabel}</h3>
                  <p>{analysis.realTeam || analysis.teamLabel}</p>
                </div>
              </div>

              {analysis.description && (
                <div className="player-bio">
                  <p>{analysis.description.substring(0, 300)}...</p>
                </div>
              )}

              <div className="overview-grid">
                <div className="overview-item">
                  <span className="label">Nationality:</span>
                  <span className="value">
                    {analysis.realNationality || 'N/A'}
                    {analysis.realNationality && <span className="source-badge external">TheSportsDB</span>}
                  </span>
                </div>
                <div className="overview-item">
                  <span className="label">Born:</span>
                  <span className="value">
                    {analysis.birthDate || 'N/A'}
                    {analysis.birthDate && <span className="source-badge external">TheSportsDB</span>}
                  </span>
                </div>
                <div className="overview-item">
                  <span className="label">Position:</span>
                  <span className="value">
                    {analysis.position || analysis.positionLabel || 'N/A'}
                    <span className="source-badge local">KG</span>
                  </span>
                </div>
                <div className="overview-item">
                  <span className="label">Total Goals:</span>
                  <span className="value highlight">
                    {analysis.totalGoals || 0}
                    <span className="source-badge local">Local KG</span>
                  </span>
                </div>
                <div className="overview-item">
                  <span className="label">Total Assists:</span>
                  <span className="value highlight">
                    {analysis.totalAssists || 0}
                    <span className="source-badge local">Local KG</span>
                  </span>
                </div>
                <div className="overview-item">
                  <span className="label">Avg Rating:</span>
                  <span className="value highlight">
                    {analysis.avgRating?.toFixed(2) || 'N/A'}
                    <span className="source-badge local">Local KG</span>
                  </span>
                </div>
                <div className="overview-item">
                  <span className="label">Data Sources:</span>
                  <span className="value sources">{analysis.dataSources?.join(', ') || 'Local KG'}</span>
                </div>
              </div>
            </div>

            <style>{`
                .overview-content {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }
                .overview-header {
                    display: flex;
                    gap: 2rem;
                    align-items: center;
                    background: rgba(255,255,255,0.05);
                    padding: 1.5rem;
                    border-radius: var(--radius-md);
                }
                .player-photo {
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 3px solid var(--text-accent);
                    background: var(--bg-primary);
                }
                .player-bio {
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                    line-height: 1.6;
                    padding: 1rem;
                    background: rgba(0,0,0,0.2);
                    border-radius: var(--radius-sm);
                    border-left: 3px solid var(--primary);
                }
                .player-title h3 {
                    font-size: 2rem;
                    margin: 0;
                    color: var(--text-primary);
                }
                .player-title p {
                    font-size: 1.2rem;
                    color: var(--text-accent);
                    margin: 0;
                }
            `}</style>
          </div>

          {/* Career Highlight */}
          {analysis.careerHighlight && (
            <div className="analysis-card highlight-card">
              <h2>🏆 Career Highlight</h2>
              <div className="highlight-content">
                <p>{analysis.careerHighlight}</p>
              </div>
            </div>
          )}

          {/* Performance Radar Chart */}
          {analysis.stats && (
            <div className="analysis-card">
              <div className="card-header-with-badge">
                <h2>Performance Profile</h2>
                <span className="source-badge local">Local KG</span>
              </div>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={prepareRadarData(analysis.stats)}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar
                    name="Performance"
                    dataKey="value"
                    stroke="#667eea"
                    fill="#667eea"
                    fillOpacity={0.6}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Key Insights */}
          {analysis.insights && analysis.insights.length > 0 && (
            <div className="analysis-card insights-card">
              <h2>Key Insights</h2>
              <ul className="insights-list">
                {analysis.insights.map((insight, idx) => (
                  <li key={idx} className={`insight ${insight.type || 'info'}`}>
                    <span className="insight-icon">
                      {insight.type === 'strength' ? '💪' : insight.type === 'warning' ? '⚠️' : '📊'}
                    </span>
                    <span className="insight-text">{insight.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {recommendations && (
            <div className="analysis-card recommendations-card">
              <h2>Recommendations</h2>

              {recommendations.bestPosition && (
                <div className="recommendation-section">
                  <h3>🎯 Optimal Position</h3>
                  <p className="recommendation-text">
                    Based on performance metrics, this player performs best as a <strong>{recommendations.bestPosition}</strong>.
                    {recommendations.positionReason && <span> {recommendations.positionReason}</span>}
                  </p>
                </div>
              )}

              {recommendations.teamFit && recommendations.teamFit.length > 0 && (
                <div className="recommendation-section">
                  <h3>🏆 Team Fit Analysis</h3>
                  <div className="team-fit-list">
                    {recommendations.teamFit.map((fit, idx) => (
                      <div key={idx} className="team-fit-item">
                        <span className="team-name">{fit.team}</span>
                        <span className={`fit-score ${fit.score > 70 ? 'high' : fit.score > 50 ? 'medium' : 'low'}`}>
                          {fit.score}% Fit
                        </span>
                        <span className="fit-reason">{fit.reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {recommendations.similarPlayers && recommendations.similarPlayers.length > 0 && (
                <div className="recommendation-section">
                  <h3>👥 Similar Players (Local KG)</h3>
                  <p>Players with similar performance profiles:</p>
                  <div className="similar-players">
                    {recommendations.similarPlayers.map((player, idx) => (
                      <div key={idx} className="similar-player-card">
                        <div className="player-name">{player.playerLabel}</div>
                        <div className="player-stats">
                          <span>Goals: {player.totalGoals || 0}</span>
                          <span>Assists: {player.totalAssists || 0}</span>
                          <span>Rating: {player.avgRating?.toFixed(1) || 'N/A'}</span>
                        </div>
                        <div className="similarity-score">{player.similarity}% similar</div>
                      </div>
                    ))}
                  </div>

                  {/* Comparison Chart */}
                  <div className="comparison-chart">
                    <h4>Performance Comparison</h4>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={prepareComparisonData(analysis, recommendations.similarPlayers)}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="goals" fill="#667eea" name="Goals" />
                        <Bar dataKey="assists" fill="#764ba2" name="Assists" />
                        <Bar dataKey="rating" fill="#43e97b" name="Rating" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {recommendations.improvementAreas && recommendations.improvementAreas.length > 0 && (
                <div className="recommendation-section">
                  <h3>📈 Areas for Improvement</h3>
                  <ul className="improvement-list">
                    {recommendations.improvementAreas.map((area, idx) => (
                      <li key={idx}>
                        <strong>{area.area}:</strong> {area.suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {recommendations.careerTrajectory && (
                <div className="recommendation-section">
                  <h3>📊 Career Trajectory</h3>
                  <p className="trajectory-text">{recommendations.careerTrajectory}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Analyzing player data from multiple sources...</p>
        </div>
      )}
    </div>
  )
}

export default Analysis

