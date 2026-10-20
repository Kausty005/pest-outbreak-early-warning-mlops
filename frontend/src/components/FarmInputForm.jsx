const FIELDS = [
  { name: 'N', label: 'Nitrogen (N)', hint: 'Soil nitrogen reading. Source unit is not documented.', min: 0, max: 300, step: 0.01 },
  { name: 'P', label: 'Phosphorus (P)', hint: 'Soil phosphorus reading. Source unit is not documented.', min: 0, max: 300, step: 0.01 },
  { name: 'K', label: 'Potassium (K)', hint: 'Soil potassium reading. Source unit is not documented.', min: 0, max: 400, step: 0.01 },
  { name: 'temperature', label: 'Temperature', hint: 'Source unit is not documented; enter the value matching training data.', min: -10, max: 60, step: 0.01 },
  { name: 'humidity', label: 'Humidity (%)', hint: 'Relative humidity as a percentage.', min: 0, max: 100, step: 0.01 },
  { name: 'ph', label: 'Soil pH', hint: 'pH scale, from 0 to 14.', min: 0, max: 14, step: 0.01 },
  { name: 'rainfall', label: 'Rainfall', hint: 'Source time period and unit are not documented.', min: 0, max: 1000, step: 0.01 },
]

export const initialValues = Object.fromEntries(FIELDS.map(({ name }) => [name, '']))

export default function FarmInputForm({ values, errors, loading, onChange, onSubmit }) {
  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="field-grid">
        {FIELDS.map((field) => (
          <div className="form-field" key={field.name}>
            <label htmlFor={field.name}>{field.label}</label>
            <input
              id={field.name}
              name={field.name}
              type="number"
              inputMode="decimal"
              min={field.min}
              max={field.max}
              step={field.step}
              value={values[field.name]}
              onChange={onChange}
              aria-describedby={`${field.name}-hint ${errors[field.name] ? `${field.name}-error` : ''}`}
              aria-invalid={Boolean(errors[field.name])}
              required
            />
            <small id={`${field.name}-hint`}>{field.hint}</small>
            {errors[field.name] && <p id={`${field.name}-error`} className="field-error" role="alert">{errors[field.name]}</p>}
          </div>
        ))}
      </div>
      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? 'Finding recommendation…' : 'Predict crop'}
      </button>
    </form>
  )
}
