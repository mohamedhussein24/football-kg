import { Link, useLocation } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          ⚽ Football KG
        </Link>
        <ul className="navbar-menu">
          <li>
            <Link
              to="/"
              className={`navbar-link ${isActive('/') ? 'active' : ''}`}
            >
              Home
            </Link>
          </li>
          <li>
            <Link
              to="/players"
              className={`navbar-link ${isActive('/players') ? 'active' : ''}`}
            >
              Players
            </Link>
          </li>
          <li>
            <Link
              to="/teams"
              className={`navbar-link ${isActive('/teams') ? 'active' : ''}`}
            >
              Teams
            </Link>
          </li>
          <li>
            <Link
              to="/queries"
              className={`navbar-link ${isActive('/queries') ? 'active' : ''}`}
            >
              Queries
            </Link>
          </li>
          <li>
            <Link
              to="/visualizations"
              className={`navbar-link ${isActive('/visualizations') ? 'active' : ''}`}
            >
              Visualizations
            </Link>
          </li>
          <li>
            <Link
              to="/analysis"
              className={`navbar-link ${isActive('/analysis') ? 'active' : ''}`}
            >
              Analysis
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  )
}

export default Navbar








