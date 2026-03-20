import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Users, Search } from 'lucide-react'
import { getPlayers } from '../api'
import { GlassCard, RankBadge, Spinner } from '../components/ui'

export default function Players() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const loadPlayers = useCallback((query = '') => {
    setLoading(true)
    getPlayers(query)
      .then((res) => {
        const results = res.data.results || res.data
        setPlayers(Array.isArray(results) ? results : [])
      })
      .catch(() => setPlayers([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { loadPlayers() }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    loadPlayers(search)
  }

  return (
    <div>
      <h1 className="page-title">
        <Users size={22} style={{ verticalAlign: 'middle', marginRight: 8 }} />
        Jugadores
      </h1>

      <GlassCard>
        <form onSubmit={handleSearch} style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por nombre, guild o alianza..."
                className="search-input"
                style={{ paddingLeft: '2rem', width: '100%' }}
              />
            </div>
            <button type="submit" className="btn btn-primary">Buscar</button>
          </div>
        </form>

        {loading ? (
          <Spinner />
        ) : players.length === 0 ? (
          <div className="loading-state">No se encontraron jugadores</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Guild</th>
                  <th>Alianza</th>
                  <th>Rango</th>
                  <th>Elo</th>
                </tr>
              </thead>
              <tbody className="fade-in-rows">
                {players.map((player) => (
                  <tr key={player.id}>
                    <td>
                      <Link to={`/players/${player.id}`} className="player-link">
                        {player.name}
                      </Link>
                    </td>
                    <td className="text-secondary">{player.guild_name || '--'}</td>
                    <td className="text-secondary">{player.alliance_name || '--'}</td>
                    <td>
                      {player.rank ? <RankBadge name={player.rank.name} color={player.rank.color} /> : '--'}
                    </td>
                    <td>
                      <strong className="text-gold">{player.elo || '--'}</strong>
                    </td>
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
