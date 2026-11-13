import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
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
      input_summary: { N: 90, P: 42, K: 43, temperature: 20.8, humidity: 82.0, ph: 6.5, rainfall: 202.9 },
      top_recommendations: [{ crop: 'rice', model_score: 0.92 }, { crop: 'jute', model_score: 0.05 }, { crop: 'maize', model_score: 0.03 }],
      confidence_note: 'High confidence',
      disclaimer: 'Advisory only',
      persistence_status: 'disabled',
    }),
  },
  fertilizerApi: {
    modelInfo: vi.fn().mockResolvedValue({ model_available: true, model_version: '1.1.0' }),
    example: vi.fn().mockResolvedValue({ crop: 'Rice', state_name: 'Maharashtra', nitrogen__nutrient_index: 1.5 }),
    recommend: vi.fn().mockResolvedValue({
      crop: 'Rice',
      state_name: 'Maharashtra',
      recommendations: {
        nitrogen: { value: 70, unit: 'kg/ha', chemical_form: 'N' },
        phosphorus: { value: 35, unit: 'kg/ha', chemical_form: 'P₂O₅' },
        potassium: { value: 40, unit: 'kg/ha', chemical_form: 'K₂O' },
      },
      fertilizer_commercial_equivalent_approx: {
        urea_46_pct_n_kg_ha: 152,
        dap_46_pct_p2o5_kg_ha: 76,
        mop_60_pct_k2o_kg_ha: 67,
      },
      model_version: '1.1.0',
    }),
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
        name: 'Zone A',
        area_acres: 4.5,
        soil_type: 'Clay Loam',
        active_crop: 'Rice',
        telemetry: { N: 80, P: 45, K: 40, temperature: 28, humidity: 80, ph: 6.2, rainfall: 150, soil_moisture: 72 },
        irrigation_summary: { status: 'OPTIMAL', status_color: '#10b981', urgency: 'None' },
      },
    ]),
    weather: vi.fn().mockResolvedValue({
      temperature_c: 28.4,
      humidity_pct: 62.0,
      precipitation_mm: 3.2,
      wind_speed_kmh: 14.0,
    }),
    advisory: vi.fn().mockResolvedValue({
      zone_id: 'zone-1',
      active_crop: 'Rice',
      journey_guidance: {
        irrigation: { status: 'OPTIMAL', status_color: '#10b981', action: 'Optimal', urgency: 'None' },
        crop_suitability: { ranked_alternatives: [{ crop: 'Rice', probability: 0.95 }] },
        pest_protection: { primary_pest: 'Stem Borer', risk_assessment: { risk_level: 'Low' } },
      },
    }),
    simulate: vi.fn().mockResolvedValue({ status: 'simulated' }),
  },
  pestRiskApi: {
    supportedProfiles: vi.fn().mockResolvedValue({
      supported_crops: ['cotton', 'soybean', 'rice', 'maize'],
      pests_by_crop: { cotton: [{ id: 'pink_bollworm', label: 'Pink Bollworm' }] },
      districts: ['Nagpur', 'Amravati'],
      available_date_ranges: { earliest_available_date: '2023-06-01', latest_available_date: '2023-10-31' },
    }),
    assess: vi.fn().mockResolvedValue({
      risk_assessment: { risk_level: 'Low', status_color: '#10b981', risk_score: 25 },
      environmental_conditions: {},
      explanations: { primary_driver: 'Normal humidity' },
    }),
  },
  publicAdvisoriesApi: {
    list: vi.fn().mockResolvedValue([]),
    summary: vi.fn().mockResolvedValue({ total_advisories: 0, by_crop: {}, by_severity: {} }),
  },
  pestSurveillanceApi: {
    dashboard: vi.fn().mockResolvedValue({ total_records: 0, active_hotspots: 0 }),
    records: vi.fn().mockResolvedValue([]),
    readinessGate: vi.fn().mockResolvedValue({ operational_status: 'READY' }),
  },
  lifecycleApi: {
    logEvent: vi.fn().mockResolvedValue({ status: 'recorded' }),
    history: vi.fn().mockResolvedValue([]),
  },
}))

describe('AgriAdapt Precision Agricultural Platform', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(cleanup)

  test('displays farmer sign-in modal when no session exists and authenticates with persistence', async () => {
    render(<App />)

    // Sign in modal elements
    expect(screen.getByText(/Sign In to AgriAdapt/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Farmer \/ Operator Name \*/i)).toBeInTheDocument()

    // Fill sign in form
    fireEvent.change(screen.getByLabelText(/Farmer \/ Operator Name \*/i), { target: { value: 'Kaushal Agronomist' } })
    fireEvent.click(screen.getByRole('button', { name: /Enter Precision Dashboard/i }))

    // Modal disappears and onboarding wizard appears
    expect(screen.queryByText(/Sign In to AgriAdapt/i)).not.toBeInTheDocument()
    expect(screen.getByText(/Welcome, Kaushal Agronomist!/i)).toBeInTheDocument()
  })

  test('configures crops in onboarding and loads live telemetry dashboard', async () => {
    // Pre-seed user in localStorage
    localStorage.setItem('agri_auth_user', JSON.stringify({ name: 'Kaushal', role: 'Farm Owner / Agronomist' }))

    render(<App />)

    // Verify onboarding screen
    expect(screen.getByText(/Cultivated Crop Setup & Field Allocation/i)).toBeInTheDocument()

    // Deploy farm config
    const deployBtn = screen.getByRole('button', { name: /Deploy Farm & Activate Simulated IoT Sensors/i })
    fireEvent.click(deployBtn)

    // Real-time telemetry dashboard & navbar tabs render
    expect(await screen.findByText(/Real-Time IoT Agricultural Command Center/i)).toBeInTheDocument()
    expect(screen.getByText(/Field Telemetry & Farm Map/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^AI Advisory$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Crop Lifecycle$/i })).toBeInTheDocument()

    // Clicking AI Advisory in the top navigation renders the Unified Advisory form
    fireEvent.click(screen.getByRole('button', { name: /^AI Advisory$/i }))
    expect(screen.getAllByText(/Unified AI Crop & Nutrient Advisory/i).length).toBeGreaterThan(0)
  })

  test('different users have different farm estates and different dashboards', async () => {
    render(<App />)

    // Select Kaushal Sharma preset via Load Estate button
    const loadButtons = screen.getAllByRole('button', { name: /Load Estate/i })
    fireEvent.click(loadButtons[0]) // Kaushal Sharma

    expect(await screen.findByText(/Kaushal Sharma's Maharashtra Estate/i)).toBeInTheDocument()
    expect(screen.getByText(/12.5 Cultivated Acres/i)).toBeInTheDocument()

    // Switch Farmer action opens selector
    fireEvent.click(screen.getByRole('button', { name: /Switch Farmer/i }))
    expect(screen.getByText(/Sign In to AgriAdapt/i)).toBeInTheDocument()

    // Select Ramesh Patel preset (2nd button)
    const switchLoadButtons = screen.getAllByRole('button', { name: /Load Estate/i })
    fireEvent.click(switchLoadButtons[1]) // Ramesh Patel

    expect(await screen.findByText(/Ramesh Patel's Gujarat Estate/i)).toBeInTheDocument()
    expect(screen.getByText(/18 Cultivated Acres/i)).toBeInTheDocument()
  })
})
