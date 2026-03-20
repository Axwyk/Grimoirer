import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Component } from 'react'
import { Sidebar } from './components/layout'
import Dashboard from './pages/Dashboard'
import Leaderboard from './pages/Leaderboard'
import Battles from './pages/Fights'
import BattleDetail from './pages/BattleDetail'
import PlayerProfile from './pages/PlayerProfile'
import Players from './pages/Players'
import './index.css'

class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null } }
  static getDerivedStateFromError(error) { return { error } }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 40, color: '#f87171', fontFamily: 'monospace' }}>
          <h1>Error de React</h1>
          <pre style={{ whiteSpace: 'pre-wrap', color: '#e5e7eb' }}>
            {this.state.error.message}
          </pre>
          <pre style={{ whiteSpace: 'pre-wrap', color: '#7d8ba0', fontSize: '0.8rem' }}>
            {this.state.error.stack}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}

function App() {
  return (
    <ErrorBoundary>
    <Router>
      <div className="app">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/battles" element={<Battles />} />
            <Route path="/battles/:id" element={<BattleDetail />} />
            <Route path="/players" element={<Players />} />
            <Route path="/players/:id" element={<PlayerProfile />} />
          </Routes>
          <footer className="app-footer">&copy; 2026 Axwyk</footer>
        </main>
      </div>
    </Router>
    </ErrorBoundary>
  )
}

export default App
