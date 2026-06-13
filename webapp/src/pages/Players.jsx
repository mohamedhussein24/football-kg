import { useState, useEffect } from 'react'
import axios from 'axios'
import './Players.css'

function Players() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchPlayers = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get('/api/players')
      setPlayers(response.data)
      setLoading(false)
    } catch (err) {
      setError('Failed to fetch players. Please ensure the backend API is running on http://localhost:5000')
      setLoading(false)
      console.error('Error fetching players:', err)
    }
  }

  useEffect(() => {
    fetchPlayers()
  }, [])

  return (
    <div className="players">
      <div className="page-header">
        <h1>Players</h1>
        <button onClick={fetchPlayers} className="refresh-btn" disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading && players.length === 0 ? (
        <div className="loading">Loading players...</div>
      ) : (
        <div className="players-grid">
          {players.map((player, index) => (
            <div key={index} className="player-card">
              <h3>{player.playerLabel}</h3>
              <div className="player-info">
                <div className="info-item">
                  <span className="label">Team:</span>
                  <span className="value">{player.teamLabel || 'N/A'}</span>
                </div>
                <div className="info-item">
                  <span className="label">Total Goals:</span>
                  <span className="value">{player.totalGoals || 0}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {players.length === 0 && !loading && !error && (
        <div className="empty-state">
          <p>No players found in the knowledge graph.</p>
        </div>
      )}
    </div>
  )
}

export default Players


