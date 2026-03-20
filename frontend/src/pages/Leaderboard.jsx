import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Trophy } from 'lucide-react'
import { getRanking } from '../api'
import { GlassCard, RoleBadge, RankBadge, WeaponIcon, Spinner } from '../components/ui'

function getRowClass(index) {
  if (index === 0) return 'lb-top1'
  if (index <= 2) return 'lb-top2'
  if (index <= 9) return 'lb-top10'
  return ''
}

function getRankClass(index) {
  if (index === 0) return 'top-1'
  if (index === 1) return 'top-2'
  if (index === 2) return 'top-3'
  return ''
}

export default function Leaderboard() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getRanking()
      .then((res) => {
        const results = Array.isArray(res.data) ? res.data : res.data.results || []
        setData(results)
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h1 className="page-title">
        <Trophy size={22} /> Leaderboard
      </h1>

      {loading ? (
        <Spinner />
      ) : data.length === 0 ? (
        <div className="loading-state">No hay jugadores rankeados aun</div>
      ) : (
        <GlassCard>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Arma</th>
                  <th>Jugador</th>
                  <th>Rol</th>
                  <th>Rango</th>
                  <th>Elo</th>
                  <th>Peak</th>
                  <th>Batallas</th>
                </tr>
              </thead>
              <tbody className="fade-in-rows">
                {data.map((entry, index) => (
                  <tr key={entry.id} className={getRowClass(index)}>
                    <td>
                      <span className={`rank-num ${getRankClass(index)}`}>
                        {index + 1}
                      </span>
                    </td>
                    <td>
                      <WeaponIcon src={entry.weapon_icon} alt={entry.main_weapon} />
                    </td>
                    <td>
                      <Link to={`/players/${entry.player}`} className="player-link">
                        {entry.player_name}
                      </Link>
                    </td>
                    <td>
                      <RoleBadge role={entry.main_role} />
                    </td>
                    <td>
                      <RankBadge name={entry.rank_name} color={entry.rank_color} />
                    </td>
                    <td>
                      <strong className="text-gold">{entry.elo}</strong>
                    </td>
                    <td className="text-secondary">{entry.peak_elo}</td>
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
