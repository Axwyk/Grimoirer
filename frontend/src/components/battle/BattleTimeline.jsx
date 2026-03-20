import { Link } from 'react-router-dom'

export default function BattleTimeline({ killFeed, startTime }) {
  const battleStart = new Date(startTime).getTime()

  return (
    <div className="glass-card fade-in">
      <h2 className="section-title">Timeline</h2>
      <div className="timeline-container">
        {killFeed.map((kill, index) => {
          const elapsed = new Date(kill.timestamp).getTime() - battleStart
          const minutes = Math.floor(elapsed / 60000)
          const seconds = Math.floor((elapsed % 60000) / 1000)
          const timeLabel = `${minutes}:${seconds.toString().padStart(2, '0')}`

          return (
            <div key={kill.id} className="timeline-event">
              <div className="timeline-time">{timeLabel}</div>
              <div className="timeline-dot-line">
                <div className="timeline-dot" />
                {index < killFeed.length - 1 && <div className="timeline-line" />}
              </div>
              <div className="timeline-content">
                <div className="timeline-kill">
                  <Link to={`/players/${kill.killer_id}`} className="timeline-killer">
                    {kill.killer_name}
                  </Link>
                  <span className="timeline-arrow">vs</span>
                  <Link to={`/players/${kill.victim_id}`} className="timeline-victim">
                    {kill.victim_name}
                  </Link>
                </div>
                {kill.total_kill_fame > 0 && (
                  <span className="timeline-fame">
                    +{kill.total_kill_fame.toLocaleString()} fame
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
