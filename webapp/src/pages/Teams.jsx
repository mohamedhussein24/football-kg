import { useState, useEffect } from 'react'
import axios from 'axios'
import './Teams.css'

function Teams() {
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchTeams = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get('/api/teams')
      setTeams(response.data)
      setLoading(false)
    } catch (err) {
      setError('Failed to fetch teams. Please ensure the backend API is running on http://localhost:5000')
      setLoading(false)
      console.error('Error fetching teams:', err)
    }
  }

  useEffect(() => {
    fetchTeams()
  }, [])

  return (
    <div className="teams">
      <div className="page-header">
        <h1>Teams</h1>
        <button onClick={fetchTeams} className="refresh-btn" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading && teams.length === 0 ? (
        <div className="loading">Loading teams...</div>
      ) : (
        <div className="teams-grid">
          {teams.map((team, index) => (
            <div key={index} className="team-card">
              <h3>{team.teamLabel}</h3>
              <div className="team-info">
                <div className="info-item">
                  <span className="label">Players:</span>
                  <span className="value">{team.playerCount || 0}</span>
                </div>
                <div className="info-item">
                  <span className="label">Total Goals:</span>
                  <span className="value">{team.totalGoals || 0}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {teams.length === 0 && !loading && !error && (
        <div className="empty-state">
          <p>No teams found in the knowledge graph.</p>
        </div>
      )}
    </div>
  )
}

export default Teams


