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
