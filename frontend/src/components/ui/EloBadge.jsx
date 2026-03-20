export default function EloBadge({ value }) {
  const cls = value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'
  return (
    <span className={`elo-badge ${cls}`}>
      {value > 0 ? '+' : ''}{value}
    </span>
  )
}
