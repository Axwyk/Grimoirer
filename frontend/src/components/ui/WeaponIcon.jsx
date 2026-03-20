export default function WeaponIcon({ src, alt }) {
  if (!src) return <span className="text-muted">--</span>
  return (
    <img
      src={src}
      alt={alt || ''}
      title={alt || ''}
      className="weapon-icon"
      onError={(e) => { e.target.style.display = 'none' }}
    />
  )
}
