export default function RankBadge({ name, color }) {
  if (!name) return <span className="text-muted">--</span>
  return (
    <span className="rank-badge" style={{ borderColor: color, color }}>
      {name}
    </span>
  )
}
