export default function StatBlock({ value, label, icon: Icon, color }) {
  return (
    <div className="stat-block">
      {Icon && <Icon size={18} className="stat-block-icon" style={color ? { color } : {}} />}
      <div className="stat-block-value" style={color ? { color } : {}}>{value}</div>
      <div className="stat-block-label">{label}</div>
    </div>
  )
}
