import './Home.css'

function Home() {
  return (
    <div className="home">
      <div className="hero">
        <h1 className="hero-title">Football Knowledge Graph</h1>
        <p className="hero-subtitle">
          Explore football data through semantic web technologies
        </p>
      </div>

      <div className="features">
        <div className="feature-card">
          <div className="feature-icon">👥</div>
          <h3>Players</h3>
          <p>Browse player profiles, statistics, and performance data</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">🏆</div>
          <h3>Teams</h3>
          <p>Explore team information and player relationships</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">🔍</div>
          <h3>SPARQL Queries</h3>
          <p>Execute and visualize SPARQL queries on the knowledge graph</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">🌐</div>
          <h3>External Data</h3>
          <p>Integrate and query data from DBpedia and Wikidata</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Analysis & Recommendations</h3>
          <p>Get AI-powered insights and recommendations for players</p>
        </div>
      </div>

      <div className="info-section">
        <h2>About This Project</h2>
        <p>
          This web application provides an interface to explore a football knowledge graph
          built using RDF/OWL semantic web technologies. The knowledge graph contains
          information about players, teams, performances, and more.
        </p>
        <p>
          Navigate through the different sections to explore players, teams, and run
          SPARQL queries to discover insights from the data.
        </p>
      </div>
    </div>
  )
}

export default Home








