import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import App from '../App'

vi.mock('../services/api', () => ({
  cropApi: {
    modelInfo: vi.fn().mockResolvedValue({
      model_available: true,
      model_version: 'test-1',
      evaluation_metrics: { accuracy: 0.9, macro_f1: 0.9 },
      dataset_checksum: 'abc',
    }),
    recommend: vi.fn().mockResolvedValue({
      predicted_crop: 'rice',
      model_version: 'test-1',
      prediction_id: 'id',
      prediction_timestamp: '2025-01-01T00:00:00Z',
      input_summary: { N: 1, P: 1, K: 1, temperature: 1, humidity: 1, ph: 6, rainfall: 1 },
      top_recommendations: [{ crop: 'rice', model_score: 0.9 }],
      confidence_note: 'score note',
      disclaimer: 'disclaimer',
      persistence_status: 'disabled',
    }),
  },
  fertilizerApi: {
    modelInfo: vi.fn().mockResolvedValue({ model_available: true, model_version: '1.1.0' }),
    example: vi.fn().mockResolvedValue({ crop: 'Rice', state_name: 'Maharashtra', nitrogen__nutrient_index: 1.5 }),
    recommend: vi.fn().mockResolvedValue({ crop: 'Rice', recommendations: { nitrogen: { value: 70 } } }),
  },
  advisoryApi: {
    unified: vi.fn().mockResolvedValue({ crop_recommendation: { primary_crop: 'Rice' } }),
  },
  healthApi: {
    status: vi.fn().mockResolvedValue({ status: 'ok', crop_model_available: true, fertilizer_model_available: true }),
  },
  monitoringApi: {
    health: vi.fn().mockResolvedValue({ mlops_status: 'ok', prediction_log: { logged_inputs: 5 } }),
    latestDrift: vi.fn().mockResolvedValue({ alert: false, drift_share: 0.1, drifted_feature_count: 1 }),
    retrainHistory: vi.fn().mockResolvedValue([]),
  },
  farmApi: {
    zones: vi.fn().mockResolvedValue([
      {
        id: 'zone-1',
        name: 'Plot 1 · North Lowlands',
        area_acres: 2.5,
        soil_type: 'Clay Loam',
        active_crop: 'rice',
        telemetry: { N: 80, P: 45, K: 40, temperature: 28, humidity: 80, ph: 6.2, rainfall: 150, soil_moisture: 72 },
        irrigation_summary: { status: 'OPTIMAL', status_color: '#10b981', urgency: 'None' },
        irrigation_channel: 'Line A',
      },
    ]),
    weather: vi.fn().mockResolvedValue({
      temperature_c: 29.0,
      humidity_pct: 68.0,
      precipitation_mm: 5.0,
      wind_speed_kmh: 12.0,
    }),
    advisory: vi.fn().mockResolvedValue({
      zone_id: 'zone-1',
      active_crop: 'rice',
      journey_guidance: {
        irrigation: { status: 'OPTIMAL', status_color: '#10b981', action: 'Optimal', urgency: 'None' },
        crop_suitability: { ranked_alternatives: [{ crop: 'rice', probability: 0.95 }] },
        pest_protection: { primary_pest: 'Stem Borer', risk_assessment: { risk_level: 'Low' } },
      },
    }),
    simulate: vi.fn().mockResolvedValue({ status: 'simulated' }),
  },
  pestRiskApi: {
    supportedProfiles: vi.fn().mockResolvedValue({
      supported_crops: ['cotton', 'soybean', 'rice', 'maize'],
      available_surveillance_districts: ['Nagpur', 'Amravati', 'Yavatmal', 'Jalgaon'],
    }),
    assess: vi.fn().mockResolvedValue({
      assessment_type: 'EXPERIMENTAL_ENVIRONMENTAL_FAVORABILITY_ASSESSMENT',
      crop: 'cotton',
      pest: 'Pink Bollworm',
      scientific_name: 'Pectinophora gossypiella',
      location: 'Nagpur',
      assessment_date: '2023-09-15',
      assessment_horizon_days: 7,
      environmental_favorability_score: 0.85,
      risk_category: 'HIGH',
      risk_trend: 'RISING',
      contributing_factors: {
        favorable_drivers: ['Ambient temperature 28.5°C is in optimal window.'],
        limiting_factors: [],
      },
      environmental_observations: {
        date: '2023-09-15',
        temperature_mean_c: 28.5,
        relative_humidity_pct: 78.0,
        rainfall_mm: 5.0,
        soil_moisture_m3m3: 0.28,
        antecedent_window_days: 7,
        antecedent_mean_temperature_c: 27.8,
        antecedent_mean_humidity_pct: 75.0,
        antecedent_accumulated_rainfall_mm: 35.0,
      },
      data_quality: {
        records_used: 7,
        data_source: 'Open-Meteo & ERA5-Land',
        edaphic_data_available: true,
        phenology_data_available: true,
        missing_fields: [],
        data_notices: [],
      },
      forecast_available: true,
      forecast_summary: {
        forecast_available: true,
        forecast_source: 'Open-Meteo',
        forecast_days_count: 7,
        forecast_mean_favorability: 0.88,
        daily_projections: [
          {
            date: '2023-09-16',
            temperature_c: 29.0,
            humidity_pct: 80.0,
            rainfall_mm: 4.0,
            soil_moisture_m3m3: 0.28,
            favorability_score: 0.88,
            risk_category: 'HIGH',
          },
        ],
      },
      recommendations: ['Intensive field scouting recommended.'],
      limitations: ['Does not predict outbreak probability.'],
      references: [
        {
          title: 'Pink Bollworm Biology',
          authors: 'Fand et al.',
          year: 2021,
          institution_or_journal: 'Crop Protection',
          url: 'https://doi.org/10.1016/j.cropro.2020.105428',
          key_finding: 'Thermal thresholds established.',
        },
      ],
      disclaimer: 'This assessment evaluates environmental favorability, not statistical outbreak likelihood.',
    }),
  },
}))

afterEach(cleanup)

test('renders smart farm dashboard with 5-zone IoT grid', async () => {
  render(<App />)
  expect(await screen.findByText(/Smart Farm Command Center/i)).toBeInTheDocument()
  const plotElements = await screen.findAllByText(/Plot 1/i)
  expect(plotElements.length).toBeGreaterThan(0)
})

test('shows form validation then a server recommendation in crop tab', async () => {
  render(<App />)
  fireEvent.click(screen.getByRole('tab', { name: /crop recommendation/i }))
  fireEvent.click(screen.getByRole('button', { name: /predict crop/i }))
  expect(await screen.findAllByText(/enter a finite/i)).toHaveLength(7)
  for (const input of screen.getAllByRole('spinbutton')) fireEvent.change(input, { target: { value: '10' } })
  fireEvent.click(screen.getByRole('button', { name: /predict crop/i }))
  expect(await screen.findByRole('heading', { name: 'rice' })).toBeInTheDocument()
})

test('shows request failure in crop tab', async () => {
  const { cropApi } = await import('../services/api')
  cropApi.recommend.mockRejectedValueOnce(new Error('Service unavailable'))
  render(<App />)
  fireEvent.click(screen.getByRole('tab', { name: /crop recommendation/i }))
  for (const input of screen.getAllByRole('spinbutton')) fireEvent.change(input, { target: { value: '10' } })
  fireEvent.click(screen.getByRole('button', { name: /predict crop/i }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Service unavailable'))
})

test('renders experimental environmental pest favorability section with required disclaimers', async () => {
  render(<App />)
  // Click pest favorability tab
  fireEvent.click(screen.getByRole('tab', { name: /pest favorability/i }))

  // Verify explicit label and warning explanation
  expect(await screen.findByText(/experimental environmental favorability assessment/i)).toBeInTheDocument()
  expect(screen.getByText(/This assessment evaluates whether environmental conditions are favorable for pest activity/i)).toBeInTheDocument()
  expect(screen.getByText(/It does not predict the probability of an actual pest outbreak and is not a substitute for field surveillance/i)).toBeInTheDocument()

  // Verify form controls
  expect(screen.getByLabelText(/target crop/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/target pest species/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/district/i)).toBeInTheDocument()

  // Submit assessment request
  fireEvent.click(screen.getByRole('button', { name: /evaluate pest favorability/i }))

  // Verify results
  expect(await screen.findByText('Pink Bollworm')).toBeInTheDocument()
  expect(screen.getByText(/HIGH FAVORABILITY/i)).toBeInTheDocument()
  expect(screen.getByText(/0\.85 \/ 1\.00/i)).toBeInTheDocument()
  expect(screen.getByText(/RISING RISK/i)).toBeInTheDocument()
  expect(screen.getByText(/Ambient temperature 28\.5°C is in optimal window/i)).toBeInTheDocument()
  expect(screen.getByText(/Observed Environmental Conditions/i)).toBeInTheDocument()
  expect(screen.getByText(/Upcoming 7-Day Projections/i)).toBeInTheDocument()

  // Verify NO misleading outbreak probability metric is presented
  expect(screen.queryByText(/Outbreak Probability:/i)).not.toBeInTheDocument()
  expect(screen.queryByText(/% Outbreak/i)).not.toBeInTheDocument()
})
