import { useState, useEffect, useMemo, memo } from 'react'
import { Link } from 'react-router-dom'
import { LayoutDashboard, Users, Swords, Award, ChevronDown, TrendingUp } from 'lucide-react'
import { getStats, getRanking } from '../api'
import { GlassCard, RankBadge, Spinner } from '../components/ui'

/* ─── Group tiers by parent category ─────────────────────── */
function groupTiers(tiers) {
  const groups = []
  const map = new Map()

  for (let i = 0; i < tiers.length; i++) {
    const t = tiers[i]
    // "Hierro 3" → parent "Hierro", "Gran Maestro" → parent "Gran Maestro"
    const match = t.name.match(/^(.+?)\s+\d$/)
    const parent = match ? match[1] : t.name
    const nextMin = tiers[i + 1]?.min_elo
    const range = nextMin ? `${t.min_elo} – ${nextMin - 1}` : `${t.min_elo}+`

    if (!map.has(parent)) {
      const group = { parent, color: t.color, children: [] }
      map.set(parent, group)
      groups.push(group)
    }
    map.get(parent).children.push({ ...t, range })
  }
  return groups
}

/* ─── Rank Medal (LoL-style emblem) ──────────────────────── */
const RankCategoryBlock = memo(function RankCategoryBlock({ group }) {
  const [open, setOpen] = useState(false)
  const { parent, color, children } = group
  const hasSubs = children.length > 1

  return (
    <div className={`rank-medal ${open ? 'is-open' : ''}`} onClick={() => setOpen((v) => !v)}>
      <div className="rank-medal-emblem" style={{ '--rank-color': color }}>
        <div className="rank-medal-hex">
          <span className="rank-medal-icon">{parent.charAt(0)}</span>
        </div>
        <div className="rank-medal-glow" />
      </div>
      <div className="rank-medal-label" style={{ color }}>{parent}</div>
      <div className="rank-medal-elo">{children[0].min_elo}+</div>
      <ChevronDown size={12} className={`rank-medal-chevron ${open ? 'open' : ''}`} />
      {open && (
        <div className="rank-medal-dropdown">
          {hasSubs ? (
            children.map((sub) => (
              <div key={sub.name} className="tier-sub-row">
                <span className="tier-sub-name" style={{ color }}>{sub.name}</span>
                <span className="tier-sub-range">{sub.range}</span>
              </div>
            ))
          ) : (
            <div className="tier-sub-row">
              <span className="tier-sub-name" style={{ color }}>ELO</span>
              <span className="tier-sub-range">{children[0].range}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
})

/* ─── Stat card ──────────────────────────────────────────── */
const STAT_ITEMS = [
  { key: 'total_players', icon: Users, label: 'Jugadores', color: 'var(--accent-blue)' },
  { key: 'total_battles', icon: Swords, label: 'Batallas', color: 'var(--accent-red)' },
  { key: 'total_events', icon: TrendingUp, label: 'Eventos', color: 'var(--accent-green)' },
  { key: 'ranked_players', icon: Award, label: 'Rankeados', color: 'var(--accent-gold)' },
]

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [top5, setTop5] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getStats(), getRanking()])
      .then(([statsRes, rankingRes]) => {
        setStats(statsRes.data)
        const list = Array.isArray(rankingRes.data) ? rankingRes.data : rankingRes.data.results || []
        setTop5(list.slice(0, 5))
      })
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [])

  const tierGroups = useMemo(
    () => groupTiers(stats?.rank_tiers || []),
    [stats?.rank_tiers]
  )

  if (loading) return <Spinner />
  if (!stats) return <div className="loading-state">Error al cargar estadisticas</div>

  return (
    <div>
      <h1 className="page-title">
        <LayoutDashboard size={22} /> Dashboard
      </h1>

      {stats.tracked_guild && (
        <GlassCard>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.3rem', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
              Gremio rastreado
            </div>
            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-gold)' }}>
              {stats.tracked_guild}
            </div>
          </div>
        </GlassCard>
      )}

      <div className="stats-grid">
        {STAT_ITEMS.map((s) => (
          <div key={s.key} className="stat-block fade-in">
            <s.icon size={18} style={{ color: s.color, marginBottom: '0.3rem' }} />
            <div className="stat-block-value" style={{ color: s.color }}>{stats[s.key]}</div>
            <div className="stat-block-label">{s.label}</div>
          </div>
        ))}
      </div>

      {tierGroups.length > 0 && (
        <GlassCard>
          <h2 className="section-title">Sistema de Rangos</h2>
          <div className="rank-tiers-grid">
            {tierGroups.map((group) => (
              <RankCategoryBlock key={group.parent} group={group} />
            ))}
          </div>
        </GlassCard>
      )}

      {top5.length > 0 && (
        <GlassCard>
          <div className="card-header">
            <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>Top 5 Jugadores</h2>
            <Link to="/leaderboard" className="btn btn-sm btn-primary">Ver ranking completo</Link>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Jugador</th>
                  <th>Guild</th>
                  <th>Rango</th>
                  <th>Elo</th>
                  <th>Batallas</th>
                </tr>
              </thead>
              <tbody>
                {top5.map((entry, index) => (
                  <tr key={entry.id}>
                    <td>
                      <span className={`rank-num ${index === 0 ? 'top-1' : index === 1 ? 'top-2' : index === 2 ? 'top-3' : ''}`}>
                        {index + 1}
                      </span>
                    </td>
                    <td>
                      <Link to={`/players/${entry.player}`} className="player-link">{entry.player_name}</Link>
                    </td>
                    <td className="text-secondary">{entry.player_guild || '--'}</td>
                    <td>
                      <RankBadge name={entry.rank_name} color={entry.rank_color} />
                    </td>
                    <td><strong className="text-gold">{entry.elo}</strong></td>
                    <td>{entry.total_battles}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}
    </div>
  )
}
