import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import AuthModal from './components/AuthModal'
import FarmSetupWizard from './components/FarmSetupWizard'
import FarmDashboard from './components/FarmDashboard'
import UnifiedInputPanel from './components/UnifiedInputPanel'
import LifecycleMonitor from './components/LifecycleMonitor'
import EnvironmentalPestRiskSection from './components/EnvironmentalPestRiskSection'
import PublicPestAdvisoriesSection from './components/PublicPestAdvisoriesSection'
import FieldSurveillanceSection from './components/FieldSurveillanceSection'
import MLOpsStatus from './components/MLOpsStatus'
import { getFarmStorageKeyForUser, ensurePresetFarmsInitialized, simulateTelemetryForCrop } from './utils/userFarmStorage'

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('agri_auth_user')
    if (saved) {
      try { return JSON.parse(saved) } catch {}
    }
    return null
  })

  const [farmProfile, setFarmProfile] = useState(() => {
    const savedUser = localStorage.getItem('agri_auth_user')
    if (savedUser) {
      try {
        const u = JSON.parse(savedUser)
        const key = getFarmStorageKeyForUser(u)
        const savedFarm = localStorage.getItem(key) || localStorage.getItem('agri_active_farm_config')
        if (savedFarm) return JSON.parse(savedFarm)
      } catch {}
    }
    return null
  })

  const [isAuthOpen, setIsAuthOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [selectedCropDetail, setSelectedCropDetail] = useState(null)
  const [selectedZone, setSelectedZone] = useState(null)
  const [activeTelemetry, setActiveTelemetry] = useState(null)

  // Ensure preset farmers are available in storage
  useEffect(() => {
    ensurePresetFarmsInitialized()
  }, [])

  // Sync farm profile whenever the active logged-in farmer changes
  useEffect(() => {
    if (!currentUser) {
      setFarmProfile(null)
      setSelectedZone(null)
      setActiveTelemetry(null)
      return
    }
    const key = getFarmStorageKeyForUser(currentUser)
    const saved = localStorage.getItem(key)
    if (saved) {
      try {
        const profile = JSON.parse(saved)
        setFarmProfile(profile)
        if (profile.zones && profile.zones.length > 0) {
          setSelectedZone(profile.zones[0])
          setActiveTelemetry(simulateTelemetryForCrop(profile.zones[0].crop))
        }
        return
      } catch {}
    }
    // If user has no farm yet, prompt them to configure
    setFarmProfile(null)
    setSelectedZone(null)
    setActiveTelemetry(null)
  }, [currentUser?.id, currentUser?.name])

  const handleLogin = (user) => {
    setCurrentUser(user)
    setIsAuthOpen(false)
    const key = getFarmStorageKeyForUser(user)
    const saved = localStorage.getItem(key)
    if (saved) {
      try {
        const profile = JSON.parse(saved)
        setFarmProfile(profile)
        if (profile.zones && profile.zones.length > 0) {
          setSelectedZone(profile.zones[0])
          setActiveTelemetry(simulateTelemetryForCrop(profile.zones[0].crop))
        }
        return
      } catch {}
    }
    setFarmProfile(null)
  }

  const handleLogout = () => {
    localStorage.removeItem('agri_auth_user')
    setCurrentUser(null)
    setFarmProfile(null)
    setSelectedZone(null)
    setActiveTelemetry(null)
    setIsAuthOpen(false)
  }

  const handleFarmConfigured = (profile) => {
    if (currentUser) {
      const key = getFarmStorageKeyForUser(currentUser)
      localStorage.setItem(key, JSON.stringify(profile))
    }
    localStorage.setItem('agri_active_farm_config', JSON.stringify(profile))
    setFarmProfile(profile)
    if (profile.zones && profile.zones.length > 0) {
      setSelectedZone(profile.zones[0])
      const initialTele = simulateTelemetryForCrop(profile.zones[0].crop)
      setActiveTelemetry(initialTele)
    }
  }

  const handleReconfigureFarm = () => {
    if (currentUser) {
      const key = getFarmStorageKeyForUser(currentUser)
      localStorage.removeItem(key)
    }
    setFarmProfile(null)
    setSelectedZone(null)
    setActiveTelemetry(null)
  }

  const handleSelectCropForDetail = (cropName) => {
    setSelectedCropDetail(cropName)
    setActiveTab('pest-risk')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', background: 'var(--bg-app-gradient)' }}>
      {/* User Authentication Modal (Prompt on initial load or when switching farmer) */}
      {(!currentUser || isAuthOpen) && (
        <AuthModal
          onLogin={handleLogin}
          onCancel={currentUser ? () => setIsAuthOpen(false) : null}
        />
      )}

      {/* Main Top Navigation */}
      <Navbar
        currentUser={currentUser}
        onLogout={handleLogout}
        onSwitchFarmer={() => setIsAuthOpen(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main View Area */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '1.25rem 2rem 2.5rem' }}>
        {/* Onboarding Empty State: If this specific farmer has no farm config yet */}
        {!farmProfile ? (
          <div style={{ maxWidth: '960px', margin: '2rem auto' }}>
            <div style={{
              background: '#FFFFFF',
              border: '2px solid #CBD5BF',
              borderRadius: '16px',
              padding: '2.5rem',
              boxShadow: '0 8px 24px rgba(19, 46, 34, 0.08)',
              textAlign: 'center',
              marginBottom: '2rem',
            }}>
              <div style={{ fontSize: '2.75rem', marginBottom: '0.75rem' }}>🌱</div>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.75rem', fontWeight: 800, color: '#13241B', letterSpacing: '-0.02em' }}>
                Welcome, {currentUser?.name || 'Farmer'}! Configure Your Agricultural Estate
              </h2>
              <p style={{ margin: '0 auto', maxWidth: '620px', fontSize: '0.95rem', color: '#4B5563', lineHeight: 1.6 }}>
                Before live telemetry monitoring begins, select which crops are currently cultivated in your sectors. AgriAdapt will initialize simulated IoT soil masts and environmental sensors specifically calibrated for your crops.
              </p>
            </div>

            <FarmSetupWizard
              currentUser={currentUser}
              initialConfig={null}
              onFarmConfigured={handleFarmConfigured}
              onSelectCropForDetail={handleSelectCropForDetail}
            />
          </div>
        ) : (
          <div>
            {/* Context Subheader Bar */}
            <div style={{
              display: 'flex',
              marginBottom: '1.25rem',
              paddingBottom: '0.75rem',
              borderBottom: '1.5px solid #CBD5BF',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#13241B', letterSpacing: '-0.01em' }}>
                  {activeTab === 'dashboard' && 'Field Telemetry & Farm Map'}
                  {activeTab === 'advisory' && 'Unified AI Crop & Nutrient Advisory'}
                  {activeTab === 'lifecycle' && 'Crop Lifecycle & Health Audit'}
                  {activeTab === 'pest-risk' && 'Pest Outbreak Surveillance & Risk'}
                  {activeTab === 'public-advisories' && 'ICAR & University Research Advisories'}
                  {activeTab === 'surveillance' && 'Field Pilot Scouting Register'}
                </h2>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                <span style={{ fontSize: '0.825rem', color: '#4B5563' }}>
                  {currentUser?.name ? `${currentUser.name}'s Estate:` : 'Estate:'}{' '}
                  <strong style={{ color: '#13241B' }}>{farmProfile.primaryCrop}</strong> ({farmProfile.state})
                </span>
                <button
                  type="button"
                  className="btn-secondary-white"
                  style={{ padding: '0.4rem 0.85rem', fontSize: '0.775rem' }}
                  onClick={handleReconfigureFarm}
                >
                  ⚙️ Reconfigure Crops
                </button>
              </div>
            </div>

            {/* Tab 1: Field Dashboard & IoT Telemetry */}
            {activeTab === 'dashboard' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.35rem', alignItems: 'start' }}>
                <FarmDashboard
                  currentUser={currentUser}
                  farmProfile={farmProfile}
                  onSelectCropForDetail={handleSelectCropForDetail}
                  onTelemetryUpdate={(tele, z) => {
                    setActiveTelemetry(tele)
                    setSelectedZone(z)
                  }}
                />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.35rem' }}>
                  <MLOpsStatus />
                  <div className="modern-card" style={{ border: '1.5px solid #CBD5BF' }}>
                    <div style={{ fontSize: '0.775rem', fontWeight: 800, color: '#059669', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      {currentUser?.name ? `${currentUser.name}'s Standing Plants` : 'Active Standing Plants'}
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#13241B', marginTop: '0.2rem' }}>
                      {farmProfile.zones?.length || 3} Zones Under Cultivation
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem', marginTop: '0.85rem' }}>
                      {farmProfile.zones?.map((z, i) => (
                        <div key={i} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          padding: '0.55rem 0.75rem',
                          background: '#FAFBF6',
                          border: '1px solid #E2E8D8',
                          borderRadius: '8px',
                          fontSize: '0.825rem',
                        }}>
                          <span style={{ fontWeight: 700, color: '#13241B' }}>{z.label}: {z.crop}</span>
                          <span style={{ color: '#059669', fontWeight: 600 }}>{z.area}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Combined AI Crop Recommendation & Fertilizer */}
            {activeTab === 'advisory' && (
              <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                <UnifiedInputPanel
                  prefill={activeTelemetry}
                  farmProfile={farmProfile}
                />
              </div>
            )}

            {/* Tab 3: End-of-Lifecycle Health & Outcome Audit */}
            {activeTab === 'lifecycle' && (
              <div style={{ maxWidth: '960px', margin: '0 auto' }}>
                <div className="modern-card" style={{ border: '1.5px solid #CBD5BF' }}>
                  <LifecycleMonitor
                    zone={selectedZone || farmProfile.zones?.[0]}
                    currentTelemetry={activeTelemetry}
                  />
                </div>
              </div>
            )}

            {/* Tab 4: Pest Outbreak Risk Engine */}
            {activeTab === 'pest-risk' && (
              <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
                <EnvironmentalPestRiskSection preselectedCrop={selectedCropDetail} />
              </div>
            )}

            {/* Tab 5: Public Advisories from ICAR/KVK */}
            {activeTab === 'public-advisories' && (
              <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
                <PublicPestAdvisoriesSection />
              </div>
            )}

            {/* Tab 6: Field Scouting Surveillance */}
            {activeTab === 'surveillance' && (
              <div style={{ maxWidth: '1140px', margin: '0 auto' }}>
                <FieldSurveillanceSection />
              </div>
            )}
          </div>
        )}
      </main>

      {/* Subtle Professional Footer */}
      <footer style={{
        backgroundColor: '#FAFBF6',
        borderTop: '1.5px solid #CBD5BF',
        padding: '0.75rem 2rem',
        fontSize: '0.775rem',
        color: '#4B5563',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <div style={{ fontWeight: 600 }}>
          AgriAdapt AI · Autonomous Precision Agriculture & Biophysical Intelligence Platform
        </div>
        <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
          <span>Model Version: <code style={{ background: '#ECFDF5', color: '#047857', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>v1.2.0</code></span>
          <span>Engine Status: <code style={{ background: '#E0F2FE', color: '#0369A1', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>Active</code></span>
        </div>
      </footer>
    </div>
  )
}
