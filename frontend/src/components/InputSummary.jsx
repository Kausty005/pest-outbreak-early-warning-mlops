const LABELS = { N: 'Nitrogen', P: 'Phosphorus', K: 'Potassium', temperature: 'Temperature', humidity: 'Humidity', ph: 'Soil pH', rainfall: 'Rainfall' }

export default function InputSummary({ summary }) {
  if (!summary) return null
  return (
    <section className="input-summary">
      <h3>Submitted values</h3>
      <dl>
        {Object.entries(summary).map(([name, value]) => <div key={name}><dt>{LABELS[name]}</dt><dd>{value}</dd></div>)}
      </dl>
    </section>
  )
}
