import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Trophy, Swords, Users } from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/leaderboard', icon: Trophy, label: 'Leaderboard' },
  { to: '/battles', icon: Swords, label: 'Batallas' },
  { to: '/players', icon: Users, label: 'Jugadores' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>ELO ALBION</h1>
        <span>ZvZ Roaming Rankings</span>
      </div>
      <nav>
        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink key={to} to={to} end={end}>
            <Icon size={18} />
            <span className="nav-label">{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
