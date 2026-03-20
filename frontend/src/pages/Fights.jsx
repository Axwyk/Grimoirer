import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Swords, CheckCircle, Clock, Minus } from 'lucide-react'
import { getBattles } from '../api'
import { GlassCard, Spinner } from '../components/ui'

export default function Battles() {
  const [battles, setBattles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getBattles()
      .then((res) => {
        const results = res.data.results || res.data
        setBattles(Array.isArray(results) ? results : [])
      })
      .catch(() => setBattles([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div>
      <h1 className="page-title">
        <Swords size={22} /> Batallas
      </h1>

      {battles.length === 0 ? (
        <div className="loading-state">No hay batallas registradas aun</div>
      ) : (
        <GlassCard>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Fecha</th>
                  <th>Jugadores</th>
                  <th>Kills</th>
                  <th>Guilds</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody className="fade-in-rows">
                {battles.map((battle) => (
                  <tr key={battle.id}>
                    <td>
                      <Link to={`/battles/${battle.id}`} className="player-link">#{battle.id}</Link>
                    </td>
                    <td className="text-secondary">
                      {new Date(battle.start_time).toLocaleString('es')}
                    </td>
                    <td>
                      <strong className="text-blue">{battle.total_players}</strong>
                    </td>
                    <td>
                      <strong style={{ color: 'var(--accent-red)' }}>{battle.total_kills}</strong>
                    </td>
                    <td>{battle.total_guilds}</td>
                    <td>
                      {battle.elo_updated ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: 'var(--accent-green)', fontSize: '0.8rem', fontWeight: 600 }}>
                          <CheckCircle size={13} /> Procesado
                        </span>
                      ) : battle.processed ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: 'var(--accent-gold)', fontSize: '0.8rem', fontWeight: 600 }}>
                          <Clock size={13} /> Stats
                        </span>
                      ) : (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                          <Minus size={13} /> Pendiente
                        </span>
                      )}
                    </td>
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
