export default function RoleBadge({ role }) {
  const display = role || 'DPS'
  return <span className={`role-badge ${display}`}>{display}</span>
}
