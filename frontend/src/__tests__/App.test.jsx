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
  pestForecastApi: {
    info: vi.fn().mockResolvedValue({
      available_models: [{ model_type: 'full', label: 'Full Model', decision_threshold: 0.72, available: true }],
      crop_pest_pairs: { Maize: 'Fall armyworm' },
      growth_stages_by_crop: { Maize: ['V1_V4_early_whorl'] },
      sample_districts: ['Davanagere'],
      disclaimer: 'Synthetic data only',
    }),
    example: vi.fn().mockResolvedValue({
      crop: 'Maize',
      pest: 'Fall armyworm',
      district: 'Davanagere',
      growth_stage: 'V5_V8_mid_whorl',
      model_type: 'full',
      t7_mean_temp_c: 28.5,
      t7_min_temp_c: 22.0,
      t7_max_temp_c: 35.0,
      t7_mean_rh_pct: 78.0,
      t7_high_rh_days: 3,
      t7_rainfall_mm: 35.0,
      t14_rainfall_mm: 65.0,
      current_incidence_pct_t0: 4.5,
      current_severity_pct_t0: 2.1,
      pest_present_t0: 1,
    }),
    predict: vi.fn().mockResolvedValue({
      crop: 'Maize',
      target_pest: 'Fall armyworm',
      forecast_horizon: '7 days',
      outbreak_probability: 0.8065,
      outbreak_predicted: true,
      risk_level: 'HIGH OUTBREAK RISK',
      decision_threshold: 0.72,
      model_used: 'full',
      model_label: 'Full-Feature Forecasting Model',
      features_used: ['crop', 'pest'],
      disclaimer: 'Synthetic data only',
      input_summary: { crop: 'Maize' },
    }),
  },
  healthApi: {
    status: vi.fn().mockResolvedValue({ status: 'ok', crop_model_available: true, fertilizer_model_available: true }),
  },
}))

afterEach(cleanup)

test('shows form validation then a server recommendation', async () => {
  render(<App />)
  fireEvent.click(screen.getByRole('button', { name: /predict crop/i }))
  expect(await screen.findAllByText(/enter a finite/i)).toHaveLength(7)
  for (const input of screen.getAllByRole('spinbutton')) fireEvent.change(input, { target: { value: '10' } })
  fireEvent.click(screen.getByRole('button', { name: /predict crop/i }))
  expect(await screen.findByRole('heading', { name: 'rice' })).toBeInTheDocument()
})

test('shows request failure', async () => {
  const { cropApi } = await import('../services/api')
  cropApi.recommend.mockRejectedValueOnce(new Error('Service unavailable'))
  render(<App />)
  for (const input of screen.getAllByRole('spinbutton')) fireEvent.change(input, { target: { value: '10' } })
  fireEvent.click(screen.getByRole('button', { name: /predict crop/i }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Service unavailable'))
})

test('navigates to pest outbreak forecasting tab and renders forecaster', async () => {
  render(<App />)
  fireEvent.click(screen.getByRole('tab', { name: /pest outbreak forecaster/i }))
  expect(await screen.findByRole('heading', { name: /simulated field pest forecaster/i })).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: /forecast outbreak risk/i }))
  expect(await screen.findByText(/high outbreak risk/i)).toBeInTheDocument()
  expect(
    screen.getByText(/simulated model conditions indicate elevated outbreak risk within the next 7 days/i)
  ).toBeInTheDocument()
  expect(screen.queryByText(/SYNTHETIC DATA DISCLAIMER/i)).not.toBeInTheDocument()
})

test('renders low risk simulated model output description correctly', async () => {
  const { pestForecastApi } = await import('../services/api')
  pestForecastApi.predict.mockResolvedValueOnce({
    crop: 'Rice',
    target_pest: 'Brown planthopper',
    forecast_horizon: '7 days',
    outbreak_probability: 0.22,
    outbreak_predicted: false,
    risk_level: 'LOW RISK',
    decision_threshold: 0.42,
    model_used: 'weather_crop',
    model_label: 'Weather & Crop Model',
    features_used: ['crop', 'pest'],
    disclaimer: 'Synthetic data only',
  })
  render(<App />)
  fireEvent.click(screen.getByRole('tab', { name: /pest outbreak forecaster/i }))
  fireEvent.click(screen.getByRole('button', { name: /forecast outbreak risk/i }))
  expect(await screen.findByText(/low \/ normal risk/i)).toBeInTheDocument()
  expect(
    screen.getByText(/simulated model conditions indicate outbreak probability remains below the warning threshold for the next 7 days/i)
  ).toBeInTheDocument()
  expect(screen.queryByText(/SYNTHETIC DATA DISCLAIMER/i)).not.toBeInTheDocument()
})

