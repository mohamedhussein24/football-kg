import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Players from './pages/Players'
import Teams from './pages/Teams'
import Queries from './pages/Queries'
import Visualizations from './pages/Visualizations'
import Analysis from './pages/Analysis'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/players" element={<Players />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/queries" element={<Queries />} />
            <Route path="/visualizations" element={<Visualizations />} />
            <Route path="/analysis" element={<Analysis />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App








