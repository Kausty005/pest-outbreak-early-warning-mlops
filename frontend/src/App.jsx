import { useEffect, useState } from 'react'
import Navbar from './components/Navbar'
import FarmInputForm, { initialValues } from './components/FarmInputForm'
import InputSummary from './components/InputSummary'
import ModelInformation from './components/ModelInformation'
import RecommendationCard from './components/RecommendationCard'
import FertilizerSection from './components/FertilizerSection'
import UnifiedAdvisorySection from './components/UnifiedAdvisorySection'
import MonitoringSection from './components/MonitoringSection'
import PestForecastSection from './components/PestForecastSection'
import { cropApi } from './services/api'

function validate(values) {
  return Object.fromEntries(Object.entries(values).flatMap(([name, value]) => {
    if (value === '' || !Number.isFinite(Number(value))) return [[name, 'Enter a finite numeric value.']]
    return []
  }))
}

export default function App() {
  const [activeTab, setActiveTab] = useState('crop')
  const [selectedCropForFertilizer, setSelectedCropForFertilizer] = useState(null)

  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [requestError, setRequestError] = useState('')
  const [modelInfo, setModelInfo] = useState(null)
  const [modelError, setModelError] = useState('')

  const loadModelInfo = async () => {
    setModelError('')
    try { setModelInfo(await cropApi.modelInfo()) } catch (error) { setModelError(error.message) }
  }
  useEffect(() => { loadModelInfo() }, [])

  const onChange = (event) => {
    const { name, value } = event.target
    setValues((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: undefined }))
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    const nextErrors = validate(values)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return
    setLoading(true)
    setRequestError('')
    try {
      const response = await cropApi.recommend(Object.fromEntries(Object.entries(values).map(([key, value]) => [key, Number(value)])))
      setResult(response)
      loadModelInfo()
    } catch (error) { setRequestError(error.message) } finally { setLoading(false) }
  }

  const handleSelectCropForFertilizer = (cropName) => {
    setSelectedCropForFertilizer(cropName)
    setActiveTab('fertilizer')
  }

  return (
    <>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main id="home">
        <section className="hero">
          <div>
            <p className="eyebrow">AgriAdapt MLOps Agricultural Platform</p>
            <h1>Intelligent Crop Selection, Fertilizer Sizing & Pest Early-Warning.</h1>
          </div>
          <p>
            An integrated machine learning system combining calibrated crop recommendation, Indian soil nutrient index fertilizer modeling, and pest early-warning surveillance.
          </p>
        </section>

        {/* Tab Navigation */}
        <div className="tab-nav" role="tablist" aria-label="Advisory Modules">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'crop'}
            className={`tab-btn ${activeTab === 'crop' ? 'active' : ''}`}
            onClick={() => setActiveTab('crop')}
          >
            🌱 Crop Recommendation
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'fertilizer'}
            className={`tab-btn ${activeTab === 'fertilizer' ? 'active' : ''}`}
            onClick={() => setActiveTab('fertilizer')}
          >
            🧪 Fertilizer Intelligence
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'pest-forecast'}
            className={`tab-btn ${activeTab === 'pest-forecast' ? 'active' : ''}`}
            onClick={() => setActiveTab('pest-forecast')}
          >
            🐛 Pest Outbreak Forecaster
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'unified'}
            className={`tab-btn ${activeTab === 'unified' ? 'active' : ''}`}
            onClick={() => setActiveTab('unified')}
          >
            🌾 Unified & Pest Advisory
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'monitoring'}
            className={`tab-btn ${activeTab === 'monitoring' ? 'active' : ''}`}
            onClick={() => setActiveTab('monitoring')}
          >
            📡 MLOps Drift & Pipeline
          </button>
        </div>

        {/* Tab 1: Crop Recommendation */}
        {activeTab === 'crop' && (
          <div className="content-grid" id="recommendation">
            <section className="form-panel">
              <p className="eyebrow">Farm inputs</p>
              <h2>Describe the current conditions</h2>
              <FarmInputForm values={values} errors={errors} loading={loading} onChange={onChange} onSubmit={onSubmit} />
              {requestError && <div className="request-error" role="alert"><p>{requestError}</p><button onClick={onSubmit}>Retry request</button></div>}
            </section>
            <aside>
              <RecommendationCard result={result} onSelectCropForFertilizer={handleSelectCropForFertilizer} />
              <InputSummary summary={result?.input_summary} />
              {!result && <div className="empty-result"><p>Enter all seven values to view ranked crop candidates.</p></div>}
            </aside>
          </div>
        )}

        {/* Tab 2: Fertilizer Recommendation */}
        {activeTab === 'fertilizer' && (
          <FertilizerSection preselectedCrop={selectedCropForFertilizer} />
        )}

        {/* Tab 3: 7-Day Pest Outbreak Forecasting Prototype */}
        {activeTab === 'pest-forecast' && (
          <PestForecastSection />
        )}

        {/* Tab 4: Unified Advisory & Pest Early Warning */}
        {activeTab === 'unified' && (
          <UnifiedAdvisorySection />
        )}

        {/* Tab 5: MLOps Drift & Retrain Lifecycle */}
        {activeTab === 'monitoring' && (
          <MonitoringSection />
        )}

        <ModelInformation info={modelInfo} error={modelError} onRetry={loadModelInfo} />
      </main>
      <footer>
        Fieldwise Advisory · AgriAdapt AI MLOps Platform · Crop recommendation, fertilizer dosage sizing, and pest outbreak early-warning lifecycle.
      </footer>
    </>
  )
}
