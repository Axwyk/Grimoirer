import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPlayers, createPlayer, createFight } from '../api'

const ROLES = [
  { key: 'TANK', label: 'Tanque' },
  { key: 'HEALER', label: 'Healer' },
  { key: 'SUPPORT', label: 'Soporte' },
  { key: 'DPS', label: 'DPS' },
]

const emptyParticipant = () => ({
  player: '',
  role: 'DPS',
  kill_fame: 0,
  deaths: 0,
  healing_done: 0,
  damage_done: 0,
  assists: 0,
})

export default function NewFight() {
  const navigate = useNavigate()
  const [players, setPlayers] = useState([])
  const [fight, setFight] = useState({
    title: '',
    date: new Date().toISOString().slice(0, 16),
    notes: '',
  })
  const [participants, setParticipants] = useState([emptyParticipant()])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const [showNewPlayer, setShowNewPlayer] = useState(false)
  const [newPlayerName, setNewPlayerName] = useState('')
  const [newPlayerGuild, setNewPlayerGuild] = useState('')

  useEffect(() => {
    getPlayers().then((res) => {
      const results = res.data.results || res.data
      setPlayers(Array.isArray(results) ? results : [])
    })
  }, [])

  const addParticipant = () => {
    setParticipants([...participants, emptyParticipant()])
  }

  const removeParticipant = (index) => {
    setParticipants(participants.filter((_, i) => i !== index))
  }

  const updateParticipant = (index, field, value) => {
    const updated = [...participants]
    updated[index] = { ...updated[index], [field]: value }
    setParticipants(updated)
  }

  const handleAddPlayer = async () => {
    if (!newPlayerName.trim()) return
    try {
      const res = await createPlayer({
        name: newPlayerName.trim(),
        guild: newPlayerGuild.trim(),
      })
      setPlayers([...players, res.data])
      setNewPlayerName('')
      setNewPlayerGuild('')
      setShowNewPlayer(false)
    } catch {
      setError('Error al crear jugador. Puede que ya exista.')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const validParticipants = participants.filter((p) => p.player)
    if (validParticipants.length < 1) {
      setError('Se necesita al menos 1 participante')
      return
    }

    setSubmitting(true)
    try {
      const payload = {
        ...fight,
        participants: validParticipants.map((p) => ({
          player: Number(p.player),
          role: p.role,
          kill_fame: Number(p.kill_fame) || 0,
          deaths: Number(p.deaths) || 0,
          healing_done: Number(p.healing_done) || 0,
          damage_done: Number(p.damage_done) || 0,
          assists: Number(p.assists) || 0,
        })),
      }
      await createFight(payload)
      navigate('/fights')
    } catch (err) {
      setError(
        err.response?.data
          ? JSON.stringify(err.response.data)
          : 'Error al registrar la pelea'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">➕ Registrar Nueva Pelea</h1>

      <div className="card" style={{ marginBottom: '1rem', borderColor: 'var(--accent-blue)', background: 'rgba(59,130,246,0.05)' }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          💡 El desempeño se califica <strong>automáticamente</strong> según las estadísticas de cada jugador y su rol.
          Solo ingresa los datos de la pelea — el sistema calculará el Elo.
        </p>
      </div>

      {error && (
        <div
          className="card"
          style={{ borderColor: 'var(--accent-red)', color: 'var(--accent-red)' }}
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="card">
          <h2 style={{ marginBottom: '1rem' }}>Información de la Pelea</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>Título (opcional)</label>
              <input
                type="text"
                value={fight.title}
                onChange={(e) => setFight({ ...fight, title: e.target.value })}
                placeholder="Ej: ZvZ Carleon Road"
              />
            </div>
            <div className="form-group">
              <label>Fecha y Hora</label>
              <input
                type="datetime-local"
                value={fight.date}
                onChange={(e) => setFight({ ...fight, date: e.target.value })}
                required
              />
            </div>
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Notas</label>
              <input
                type="text"
                value={fight.notes}
                onChange={(e) => setFight({ ...fight, notes: e.target.value })}
                placeholder="Notas opcionales..."
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Participantes</h2>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className="btn btn-sm btn-primary"
                onClick={() => setShowNewPlayer(!showNewPlayer)}
              >
                {showNewPlayer ? 'Cerrar' : '+ Nuevo Jugador'}
              </button>
              <button
                type="button"
                className="btn btn-sm btn-success"
                onClick={addParticipant}
              >
                + Participante
              </button>
            </div>
          </div>

          {showNewPlayer && (
            <div
              style={{
                display: 'flex',
                gap: '0.5rem',
                marginBottom: '1rem',
                alignItems: 'flex-end',
              }}
            >
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label>Nombre</label>
                <input
                  value={newPlayerName}
                  onChange={(e) => setNewPlayerName(e.target.value)}
                  placeholder="Nombre del jugador"
                />
              </div>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label>Guild</label>
                <input
                  value={newPlayerGuild}
                  onChange={(e) => setNewPlayerGuild(e.target.value)}
                  placeholder="Guild (opcional)"
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleAddPlayer}
              >
                Crear
              </button>
            </div>
          )}

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Jugador</th>
                  <th>Rol</th>
                  <th>Kill Fame</th>
                  <th>Muertes</th>
                  <th>Sanación</th>
                  <th>Daño</th>
                  <th>Asistencias</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {participants.map((p, i) => (
                  <tr key={i}>
                    <td>
                      <select
                        value={p.player}
                        onChange={(e) =>
                          updateParticipant(i, 'player', e.target.value)
                        }
                        style={{ minWidth: '140px' }}
                      >
                        <option value="">Seleccionar...</option>
                        {players.map((player) => (
                          <option key={player.id} value={player.id}>
                            {player.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <select
                        value={p.role}
                        onChange={(e) =>
                          updateParticipant(i, 'role', e.target.value)
                        }
                      >
                        {ROLES.map((r) => (
                          <option key={r.key} value={r.key}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        value={p.kill_fame}
                        onChange={(e) =>
                          updateParticipant(i, 'kill_fame', e.target.value)
                        }
                        style={{ width: '90px' }}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        value={p.deaths}
                        onChange={(e) =>
                          updateParticipant(i, 'deaths', e.target.value)
                        }
                        style={{ width: '70px' }}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        value={p.healing_done}
                        onChange={(e) =>
                          updateParticipant(i, 'healing_done', e.target.value)
                        }
                        style={{ width: '90px' }}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        value={p.damage_done}
                        onChange={(e) =>
                          updateParticipant(i, 'damage_done', e.target.value)
                        }
                        style={{ width: '90px' }}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        value={p.assists}
                        onChange={(e) =>
                          updateParticipant(i, 'assists', e.target.value)
                        }
                        style={{ width: '70px' }}
                      />
                    </td>
                    <td>
                      {participants.length > 1 && (
                        <button
                          type="button"
                          className="btn btn-sm btn-danger"
                          onClick={() => removeParticipant(i)}
                        >
                          ✕
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-success"
          disabled={submitting}
          style={{ width: '100%', padding: '1rem', fontSize: '1rem' }}
        >
          {submitting ? 'Registrando...' : '⚔️ Registrar Pelea (Elo Automático)'}
        </button>
      </form>
    </div>
  )
}
