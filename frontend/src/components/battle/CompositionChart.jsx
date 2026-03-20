import { useMemo } from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const ROLE_COLORS = {
  DPS: '#ef4444',
  HEALER: '#10b981',
  TANK: '#3b82f6',
  SUPPORT: '#f5be0b',
}

const tooltipStyle = {
  background: 'rgba(15, 20, 35, 0.85)',
  backdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 10,
  color: '#e5e7eb',
}

export default function CompositionChart({ stats }) {
  const roleData = useMemo(() => {
    const counts = {}
    stats.forEach((s) => {
      const role = s.role || 'DPS'
      counts[role] = (counts[role] || 0) + 1
    })
    return Object.entries(counts).map(([name, value]) => ({
      name, value, color: ROLE_COLORS[name] || '#6b7280',
    }))
  }, [stats])

  return (
    <div className="glass-card fade-in">
      <h2 className="section-title">Composicion</h2>
      <ChartColumn label="Roles" data={roleData} animDelay={200} />
    </div>
  )
}

function ChartColumn({ label, data, animDelay }) {
  return (
    <div className="chart-block">
      <h3 className="chart-label">{label}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data} cx="50%" cy="50%"
            innerRadius={45} outerRadius={75}
            paddingAngle={3} dataKey="value"
            animationBegin={animDelay} animationDuration={800}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} formatter={(v, n) => [`${v} jugadores`, n]} />
        </PieChart>
      </ResponsiveContainer>
      <div className="chart-legend">
        {data.map((d) => (
          <span key={d.name} className="legend-item">
            <span className="legend-dot" style={{ background: d.color }} />
            {d.name} ({d.value})
          </span>
        ))}
      </div>
    </div>
  )
}
