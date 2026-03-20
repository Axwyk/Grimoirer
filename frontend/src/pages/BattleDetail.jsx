import { useState, useEffect, useMemo, lazy, Suspense } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Users, Skull, Castle, Timer, BarChart3, PieChart as PieIcon, Clock, ChevronUp, ChevronDown } from 'lucide-react'
import { getBattle } from '../api'
import { GlassCard, RoleBadge, EloBadge, WeaponIcon, Spinner } from '../components/ui'

const CompositionChart = lazy(() => import('../components/battle/CompositionChart'))
const BattleTimeline = lazy(() => import('../components/battle/BattleTimeline'))

function formatDuration(start, end) {
  const ms = new Date(end) - new Date(start)
  const mins = Math.floor(ms / 60000)
  const secs = Math.floor((ms % 60000) / 1000)
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
}

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function BattleDetail() {
  const { id } = useParams()
  const [battle, setBattle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('stats')
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('desc')

  useEffect(() => {
    getBattle(id)
      .then((res) => setBattle(res.data))
      .catch(() => setBattle(null))
      .finally(() => setLoading(false))
  }, [id])

  const headerStats = useMemo(() => {
    if (!battle) return []
    return [
      { label: 'Jugadores', value: battle.total_players, Icon: Users },
      { label: 'Kills', value: battle.total_kills, Icon: Skull, color: 'var(--accent-red)' },
      { label: 'Guilds', value: battle.total_guilds, Icon: Castle },
      { label: 'Duracion', value: formatDuration(battle.start_time, battle.end_time), Icon: Timer },
    ]
  }, [battle])

  const tabs = useMemo(() => [
    { key: 'stats', label: 'Estadisticas', Icon: BarChart3 },
    { key: 'composition', label: 'Composicion', Icon: PieIcon },
    { key: 'timeline', label: 'Timeline', Icon: Clock },
  ], [])

  const sortedStats = useMemo(() => {
    const s = battle?.player_stats || []
    if (!sortKey) return s
    return [...s].sort((a, b) => {
      let va = a[sortKey], vb = b[sortKey]
      if (typeof va === 'string') va = (va || '').toLowerCase()
      if (typeof vb === 'string') vb = (vb || '').toLowerCase()
      if (va < vb) return sortDir === 'asc' ? -1 : 1
      if (va > vb) return sortDir === 'asc' ? 1 : -1
      return 0
    })
  }, [battle, sortKey, sortDir])

  if (loading) return <Spinner text="Cargando batalla..." />
  if (!battle) return <div className="loading-state">Batalla no encontrada</div>

  const stats = battle.player_stats || []
  const killFeed = battle.kill_feed || []

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return null
    return sortDir === 'asc'
      ? <ChevronUp size={12} style={{ marginLeft: 2, verticalAlign: 'middle' }} />
      : <ChevronDown size={12} style={{ marginLeft: 2, verticalAlign: 'middle' }} />
  }

  return (
    <div className="battle-detail">
      <div className="battle-header fade-in">
        <div className="battle-header-top">
          <Link to="/battles" className="back-link">
            <ArrowLeft size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />
            Batallas
          </Link>
          <h1 className="battle-title">Batalla #{battle.id}</h1>
          <div className="battle-time">
            {new Date(battle.start_time).toLocaleDateString('es', {
              day: 'numeric', month: 'short', year: 'numeric',
            })}
            {' · '}
            {formatTime(battle.start_time)} — {formatTime(battle.end_time)}
          </div>
        </div>

        <div className="battle-stats-bar">
          {headerStats.map((stat) => (
            <div key={stat.label} className="battle-stat-item">
              <stat.Icon size={16} style={{ color: stat.color || 'var(--text-muted)' }} />
              <div>
                <div className="stat-val" style={stat.color ? { color: stat.color } : {}}>
                  {stat.value}
                </div>
                <div className="stat-lbl">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="battle-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`battle-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <tab.Icon size={14} style={{ verticalAlign: 'middle', marginRight: 5 }} />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'stats' && (
        <div className="fade-in">
            {stats.length === 0 ? (
              <div className="loading-state">Sin estadisticas</div>
            ) : (
              <GlassCard>
                <h2 className="section-title">Jugadores ({stats.length})</h2>
                <div className="table-container">
                  <table className="battle-table">
                    <thead>
                      <tr>
                        <th>Arma</th>
                        <th className="sortable" onClick={() => toggleSort('player_name')}>Jugador<SortIcon col="player_name" /></th>
                        <th className="sortable" onClick={() => toggleSort('role')}>Rol<SortIcon col="role" /></th>
                        <th className="sortable" onClick={() => toggleSort('player_guild')}>Guild<SortIcon col="player_guild" /></th>
                        <th className="sortable" onClick={() => toggleSort('average_item_power')}>IP<SortIcon col="average_item_power" /></th>
                        <th className="sortable" onClick={() => toggleSort('damage_done')}>Daño<SortIcon col="damage_done" /></th>
                        <th className="sortable" onClick={() => toggleSort('healing_done')}>Healing<SortIcon col="healing_done" /></th>
                        <th className="sortable" onClick={() => toggleSort('kills')}>Kills<SortIcon col="kills" /></th>
                        <th className="sortable" onClick={() => toggleSort('deaths')}>Deaths<SortIcon col="deaths" /></th>
                        <th className="sortable" onClick={() => toggleSort('assists')}>Assists<SortIcon col="assists" /></th>
                        <th className="sortable" onClick={() => toggleSort('kill_fame')}>Fame<SortIcon col="kill_fame" /></th>
                        <th className="sortable" onClick={() => toggleSort('normalized_score')}>Score<SortIcon col="normalized_score" /></th>
                        <th className="sortable" onClick={() => toggleSort('elo_change')}>Elo<SortIcon col="elo_change" /></th>
                      </tr>
                    </thead>
                    <tbody className="fade-in-rows">
                      {sortedStats.map((s) => (
                        <tr key={s.id} className="battle-row">
                          <td><WeaponIcon src={s.weapon_icon} alt={s.main_weapon} /></td>
                          <td>
                            <Link to={`/players/${s.player}`} className="player-link">
                              {s.player_name}
                            </Link>
                          </td>
                          <td><RoleBadge role={s.role} subRole={s.sub_role} /></td>
                          <td className="text-secondary">{s.player_guild || '--'}</td>
                          <td className="text-blue">
                            {s.average_item_power ? Math.round(s.average_item_power) : '--'}
                          </td>
                          <td>{s.damage_done?.toLocaleString()}</td>
                          <td>{s.healing_done?.toLocaleString()}</td>
                          <td className="text-center">{s.kills}</td>
                          <td className="text-center">{s.deaths}</td>
                          <td className="text-center">{s.assists}</td>
                          <td className="text-gold">
                            {s.kill_fame ? s.kill_fame.toLocaleString() : '--'}
                          </td>
                          <td>
                            <span className={`score-value ${s.normalized_score >= 0 ? 'positive' : 'negative'}`}>
                              {s.normalized_score?.toFixed(2)}
                            </span>
                          </td>
                          <td><EloBadge value={s.elo_change} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </GlassCard>
            )}
        </div>
      )}

      {activeTab === 'composition' && (
        <Suspense fallback={<Spinner text="Cargando composicion..." />}>
          <CompositionChart stats={stats} />
        </Suspense>
      )}

      {activeTab === 'timeline' && (
        <Suspense fallback={<Spinner text="Cargando timeline..." />}>
          {killFeed.length > 0 ? (
            <BattleTimeline killFeed={killFeed} startTime={battle.start_time} />
          ) : (
            <div className="loading-state">Sin eventos de kill</div>
          )}
        </Suspense>
      )}
    </div>
  )
}
