import { useState } from 'react'
import axios from 'axios'
import './Queries.css'

function Queries() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const exampleQueries = [
    {
      name: '1. Top Goal Scorers',
      query: `PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel (SUM(?g) AS ?totalGoals)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  ?player ont:hasPerformance ?p .
  ?p ont:scoredGoals ?g .
}
GROUP BY ?playerLabel
ORDER BY DESC(?totalGoals)
LIMIT 15`
    },
    {
      name: '2. Performance Trends',
      query: `PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel ?totalGoals ?totalAssists
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  
  {
    SELECT ?player (SUM(?g) AS ?totalGoals) (SUM(?a) AS ?totalAssists)
    WHERE {
      ?player ont:hasPerformance ?p .
      OPTIONAL { ?p ont:scoredGoals ?g }
      OPTIONAL { ?p ont:madeAssists ?a }
    }
    GROUP BY ?player
  }
}
ORDER BY DESC(?totalGoals)
LIMIT 15`
    },
    {
      name: '3. Teams with Top Performers',
      query: `PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?teamLabel ?topScorer ?topScorerGoals ?teamTotalGoals
WHERE {
  ?team a ont:Team .
  ?team rdfs:label ?teamLabel .
  
  {
    SELECT ?team (MAX(?playerGoals) AS ?topScorerGoals) ?topScorer
    WHERE {
      ?player ont:hasTeam ?team .
      ?player rdfs:label ?topScorer .
      {
        SELECT ?player (SUM(?g) AS ?playerGoals)
        WHERE {
          ?player ont:hasPerformance ?p .
          ?p ont:scoredGoals ?g .
        }
        GROUP BY ?player
      }
    }
    GROUP BY ?team ?topScorer
  }
  
  {
    SELECT ?team (SUM(?g) AS ?teamTotalGoals)
    WHERE {
      ?player ont:hasTeam ?team .
      ?player ont:hasPerformance ?p .
      ?p ont:scoredGoals ?g .
    }
    GROUP BY ?team
  }
}
ORDER BY DESC(?teamTotalGoals)`
    },
    {
      name: '4. Comprehensive Player Stats',
      query: `PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (SUM(?goals) AS ?totalGoals)
       (SUM(?assists) AS ?totalAssists)
       (AVG(?rating) AS ?avgRating)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  
  ?player ont:hasPerformance ?perf .
  OPTIONAL { ?perf ont:scoredGoals ?goals }
  OPTIONAL { ?perf ont:madeAssists ?assists }
  OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
}
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY DESC(?totalGoals)
LIMIT 20`
    },
    {
      name: '5. Teams Ranked by Multiple Criteria',
      query: `PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?teamLabel 
       (SUM(?goals) AS ?totalGoals)
       (SUM(?assists) AS ?totalAssists)
       (AVG(?goals) AS ?avgGoalsPerPlayer)
WHERE {
  ?team a ont:Team .
  ?team rdfs:label ?teamLabel .
  ?player ont:hasTeam ?team .
  OPTIONAL {
    ?player ont:hasPerformance ?p .
    OPTIONAL { ?p ont:scoredGoals ?goals }
    OPTIONAL { ?p ont:madeAssists ?assists }
  }
}
        GROUP BY ?teamLabel
        ORDER BY DESC(?totalGoals) DESC(?totalAssists)`
    },

    {
      name: '7. Goal-to-Assist Ratio',
      query: `PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (SUM(?goals) AS ?totalGoals)
       (SUM(?assists) AS ?totalAssists)
       (IF(SUM(?assists) > 0, (xsd:float(SUM(?goals)) / xsd:float(SUM(?assists))), 999) AS ?goalToAssistRatio)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  ?player ont:hasPerformance ?p .
  OPTIONAL { ?p ont:scoredGoals ?goals }
  OPTIONAL { ?p ont:madeAssists ?assists }
}
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY ASC(?goalToAssistRatio)
LIMIT 15`
    },
    {
      name: '8. Consistent Performers',
      query: `PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (AVG(?rating) AS ?avgRating)
       (AVG(?goals) AS ?avgGoals)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  ?player ont:hasPerformance ?perf .
  ?perf ont:scoredGoals ?goals .
  OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
}
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY DESC(?avgRating) DESC(?avgGoals)
LIMIT 15`
    }
  ]

  const handleQuerySubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      // Check if query contains external data source prefixes - use appropriate endpoint
      const queryUpper = query.toUpperCase()
      let endpoint = '/api/query'

      if (queryUpper.includes('DBPEDIA') || queryUpper.includes('DBO:') || queryUpper.includes('DBR:')) {
        endpoint = '/api/query/dbpedia'
      } else if (queryUpper.includes('WIKIDATA') || queryUpper.includes('WD:') || queryUpper.includes('WDT:')) {
        endpoint = '/api/query/wikidata'
      }

      const response = await axios.post(endpoint, { query })
      setResults(response.data)
      setLoading(false)
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to execute query'
      setError(`Error: ${errorMessage}. Please ensure the backend API is running on http://localhost:5000`)
      setLoading(false)
      console.error('Error executing query:', err)
    }
  }

  const loadExampleQuery = (exampleQuery) => {
    setQuery(exampleQuery.query)
  }

  const handleIntegratedQuery = async (type) => {
    setLoading(true)
    setError(null)
    setResults(null)
    setQuery(`[Executing Integrated Query: ${type === 'top_scorers_enriched' ? 'Top Scorers + Nationality' : 'Young Talents + Real Age'}]`)

    try {
      const response = await axios.post('/api/query/integrated', { type })
      setResults(response.data)
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to execute integrated query')
      setLoading(false)
    }
  }

  return (
    <div className="queries">
      <div className="page-header">
        <h1>SPARQL Queries</h1>
      </div>

      <div className="queries-container">
        <div className="query-input-section">
          <h2>Execute Query</h2>

          <div className="example-queries">
            <h3>Example Queries:</h3>
            <div className="example-buttons">
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  onClick={() => loadExampleQuery(example)}
                  className="example-btn"
                >
                  {example.name}
                </button>
              ))}
            </div>

            <h3>Integrated Data Queries (Local KG + TheSportsDB):</h3>
            <p className="integrated-info">These queries combine local performance stats with real-world data (bio, age, team).</p>
            <div className="example-buttons">
              <button onClick={() => handleIntegratedQuery('top_scorers_enriched')} className="example-btn integrated-btn">
                🏅 Enriched Top Scorers
              </button>
              <button onClick={() => handleIntegratedQuery('young_talents')} className="example-btn integrated-btn">
                🌟 Young Talents (Under 25)
              </button>

            </div>
          </div>

          <form onSubmit={handleQuerySubmit} className="query-form">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your SPARQL query here..."
              className="query-textarea"
              rows="10"
            />
            <button type="submit" className="submit-btn" disabled={loading || !query.trim()}>
              {loading ? 'Executing...' : 'Execute Query'}
            </button>
          </form>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </div>

        <div className="query-results-section">
          <h2>Results</h2>

          {loading && (
            <div className="loading">Executing query...</div>
          )}

          {results && !loading && (
            <div className="results-container">
              {results.source && (
                <div className="source-badge-result">
                  <strong>Data Source:</strong> {results.source}
                  {results.sourceUrl && (
                    <span> | <a href={results.sourceUrl} target="_blank" rel="noopener noreferrer">Visit {results.source}</a></span>
                  )}
                </div>
              )}
              {results.answer !== undefined ? (
                // ASK query result
                <div className="ask-result">
                  <p><strong>Answer:</strong> {results.answer ? 'Yes' : 'No'}</p>
                </div>
              ) : results.graph ? (
                // DESCRIBE or CONSTRUCT query result
                <div className="graph-result">
                  <h3>Graph Result (Turtle format):</h3>
                  <pre className="graph-output">{results.graph}</pre>
                </div>
              ) : results.columns && results.rows ? (
                // SELECT query result
                <div className="results-table-container">
                  <table className="results-table">
                    <thead>
                      <tr>
                        {results.columns.map((col, index) => (
                          <th key={index}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {results.rows.length > 0 ? (
                        results.rows.map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {row.map((cell, cellIndex) => (
                              <td key={cellIndex}>{cell}</td>
                            ))}
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={results.columns.length} style={{ textAlign: 'center', color: '#999' }}>
                            No results found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-results">
                  <p>Unexpected result format</p>
                </div>
              )}
            </div>
          )}

          {!results && !loading && (
            <div className="empty-results">
              <p>Execute a query to see results here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Queries


