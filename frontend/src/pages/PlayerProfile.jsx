import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { User, TrendingUp, Swords, Shield } from 'lucide-react'
import { getPlayer, getPlayerStats } from '../api'
import { GlassCard, StatBlock, RankBadge, EloBadge, WeaponIcon, Spinner } from '../components/ui'

export default function PlayerProfile() {
  const { id } = useParams()
  const [player, setPlayer] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getPlayer(id), getPlayerStats(id)])
      .then(([playerRes, historyRes]) => {
        setPlayer(playerRes.data)
        setHistory(Array.isArray(historyRes.data) ? historyRes.data : [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <Spinner text="Cargando perfil..." />
  if (!player) return <div className="loading-state">Jugador no encontrado</div>

  return (
    <div>
      <h1 className="page-title fade-in">
        <User size={22} style={{ verticalAlign: 'middle', marginRight: 8 }} />
        {player.name}
        {player.guild_name && (
          <span style={{ fontSize: '1rem', color: 'var(--text-muted)', marginLeft: 8 }}>
            [{player.guild_name}]
          </span>
        )}
      </h1>

      <div className="stats-grid">
        <GlassCard>
          <StatBlock
            icon={TrendingUp}
            value={player.elo || 600}
            label="ELO Actual"
            color="var(--accent-gold)"
          />
          {player.rank && (
            <div style={{ marginTop: '0.5rem', textAlign: 'center' }}>
              <RankBadge name={player.rank.name} color={player.rank.color} />
            </div>
          )}
        </GlassCard>
        <GlassCard>
          <StatBlock icon={TrendingUp} value={player.peak_elo || '--'} label="Peak ELO" color="var(--accent-blue)" />
        </GlassCard>
        <GlassCard>
          <StatBlock icon={Swords} value={player.total_battles || 0} label="Batallas" />
        </GlassCard>
        {player.alliance_name && (
          <GlassCard>
            <StatBlock icon={Shield} value={player.alliance_name} label="Alianza" />
          </GlassCard>
        )}
      </div>

      <GlassCard>
        <h2 className="section-title">Historial de Batallas</h2>
        {history.length === 0 ? (
          <div className="loading-state">Sin batallas registradas</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Arma</th>
                  <th>IP</th>
                  <th>Jugadores</th>
                  <th>Dano</th>
                  <th>Healing</th>
                  <th>K/D/A</th>
                  <th>Score</th>
                  <th>Elo</th>
                  <th>Cambio</th>
                </tr>
              </thead>
              <tbody className="fade-in-rows">
                {history.map((h, i) => (
                  <tr key={i}>
                    <td>
                      <Link to={`/battles/${h.battle_id}`} className="player-link">
                        {new Date(h.date).toLocaleDateString('es')}
                      </Link>
                    </td>
                    <td><WeaponIcon src={h.weapon_icon} alt={h.main_weapon} /></td>
                    <td className="text-blue">
                      {h.average_item_power ? Math.round(h.average_item_power) : '--'}
                    </td>
                    <td>{h.total_players}</td>
                    <td>{h.damage_done?.toLocaleString()}</td>
                    <td>{h.healing_done?.toLocaleString()}</td>
                    <td>
                      <span className="text-green">{h.kills}</span>
                      /
                      <span className="text-red">{h.deaths}</span>
                      /
                      <span className="text-blue">{h.assists}</span>
                    </td>
                    <td>
                      <span className={`score-value ${h.normalized_score >= 0 ? 'positive' : 'negative'}`}>
                        {h.normalized_score?.toFixed(2)}
                      </span>
                    </td>
                    <td>{h.elo_after}</td>
                    <td><EloBadge value={h.elo_change} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </div>
  )
}
