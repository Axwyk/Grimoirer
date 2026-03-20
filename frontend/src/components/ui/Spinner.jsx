export default function Spinner({ text = 'Cargando...' }) {
  return (
    <div className="loading-state">
      <div className="spinner" />
      <p>{text}</p>
    </div>
  )
}
