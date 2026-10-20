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
