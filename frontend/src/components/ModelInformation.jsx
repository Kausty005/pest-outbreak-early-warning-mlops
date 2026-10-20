export default function ModelInformation({ info, error, onRetry }) {
  return (
    <section id="model-information" className="model-information">
      <div>
        <p className="eyebrow">Model information</p>
        <h2>Evidence, not a farming guarantee</h2>
      </div>
      {error ? <div className="inline-error"><p>{error}</p><button onClick={onRetry}>Retry model details</button></div> : null}
      {info?.model_available ? (
        <div className="metric-grid">
          <div><span>Version</span><strong>{info.model_version}</strong></div>
          <div><span>Held-out accuracy</span><strong>{(info.evaluation_metrics.accuracy * 100).toFixed(1)}%</strong></div>
          <div><span>Held-out macro F1</span><strong>{info.evaluation_metrics.macro_f1.toFixed(3)}</strong></div>
          <div><span>Dataset checksum</span><strong className="checksum">{info.dataset_checksum?.slice(0, 12)}…</strong></div>
        </div>
      ) : <p className="muted">{info?.disclaimer || 'Model details will be available after training.'}</p>}
      {info?.disclaimer && <p className="disclaimer">{info.disclaimer}</p>}
    </section>
  )
}
