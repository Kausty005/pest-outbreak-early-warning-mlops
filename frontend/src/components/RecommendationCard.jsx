export default function RecommendationCard({ result, onSelectCropForFertilizer }) {
  if (!result) return null
  return (
    <section className="result-card" aria-live="polite">
      <p className="eyebrow">Primary recommendation</p>
      <h2>{result.predicted_crop}</h2>
      <p className="muted">Model version: {result.model_version}</p>
      <div className="candidate-list">
        <h3>Top candidates</h3>
        <ol>
          {result.top_recommendations.map((candidate) => (
            <li key={candidate.crop}>
              <span>{candidate.crop}</span>
              <strong>{(candidate.model_score * 100).toFixed(1)} <small>model score</small></strong>
            </li>
          ))}
        </ol>
      </div>
      <p className="confidence-note">{result.confidence_note}</p>
      <p className="disclaimer">{result.disclaimer}</p>
      {onSelectCropForFertilizer && (
        <button
          type="button"
          className="secondary-button"
          style={{
            width: '100%',
            marginTop: '1.2rem',
            borderColor: '#b9e487',
            color: '#b9e487',
            background: 'rgba(185, 228, 135, 0.12)',
            cursor: 'pointer',
          }}
          onClick={() => onSelectCropForFertilizer(result.predicted_crop)}
        >
          🧪 Optimize Fertilizer for {result.predicted_crop} →
        </button>
      )}
    </section>
  )
}
