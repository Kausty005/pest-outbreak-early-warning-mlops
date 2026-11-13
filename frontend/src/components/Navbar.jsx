import { useEffect, useState } from 'react'

export default function Navbar({ currentUser, onLogout, activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Field Telemetry' },
    { id: 'advisory', label: 'AI Advisory' },
    { id: 'lifecycle', label: 'Crop Lifecycle' },
    { id: 'pest-risk', label: 'Pest Surveillance' },
    { id: 'public-advisories', label: 'ICAR Advisories' },
    { id: 'surveillance', label: 'Field Scouting' },
  ]

  return (
    <header style={{
      background: 'linear-gradient(90deg, #0A1E14 0%, #112F21 50%, #0D261A 100%)',
      borderBottom: '2px solid rgba(16, 185, 129, 0.35)',
      padding: '0 2rem',
      height: '66px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      boxShadow: '0 4px 20px rgba(10, 30, 20, 0.4)',
      zIndex: 50,
      flexShrink: 0,
      color: '#FFFFFF',
    }}>
      {/* Brand & Tagline */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <a href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            fontSize: '1.35rem',
            background: 'linear-gradient(135deg, #10B981 0%, #047857 100%)',
            borderRadius: '12px',
            width: '40px',
            height: '40px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(16, 185, 129, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }}>
            🌿
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em' }}>
                AgriAdapt
              </span>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 800,
                color: '#6EE7B7',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                border: '1px solid rgba(52, 211, 153, 0.4)',
                borderRadius: '6px',
                padding: '0.15rem 0.5rem',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}>
                v2.1
              </span>
            </div>
            <div style={{ fontSize: '0.675rem', color: '#A7F3D0', opacity: 0.85, letterSpacing: '0.02em', fontWeight: 500 }}>
              Autonomous Precision Agriculture & Real-Time Biophysical Engine
            </div>
          </div>
        </a>

        {/* Integrated Navigation Links - Emojis removed as requested */}
        {currentUser && (
          <nav style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginLeft: '0.5rem' }}>
            {navItems.map(item => {
              const isAct = activeTab === item.id
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.45rem',
                    background: isAct ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(5, 150, 105, 0.35) 100%)' : 'transparent',
                    color: isAct ? '#A7F3D0' : '#E5E7EB',
                    border: isAct ? '1px solid rgba(52, 211, 153, 0.55)' : '1px solid transparent',
                    borderRadius: '9px',
                    padding: '0.5rem 0.95rem',
                    fontSize: '0.85rem',
                    fontWeight: isAct ? 800 : 500,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: isAct ? '0 2px 8px rgba(0, 0, 0, 0.25)' : 'none',
                  }}
                  onMouseEnter={(e) => {
                    if (!isAct) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'
                  }}
                  onMouseLeave={(e) => {
                    if (!isAct) e.currentTarget.style.background = 'transparent'
                  }}
                >
                  <span>{item.label}</span>
                  {isAct && (
                    <span style={{
                      width: 5,
                      height: 5,
                      borderRadius: '50%',
                      backgroundColor: '#34D399',
                      boxShadow: '0 0 6px #34D399',
                    }} />
                  )}
                </button>
              )
            })}
          </nav>
        )}
      </div>

      {/* Right Controls - FastAPI badge removed as requested */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* User Session Profile & Logout */}
        {currentUser && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.85rem',
            background: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '10px',
            padding: '0.35rem 0.65rem 0.35rem 0.75rem',
          }}>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
              color: '#FFFFFF',
              fontWeight: 800,
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
            }}>
              {currentUser.name ? currentUser.name.charAt(0).toUpperCase() : 'A'}
            </div>

            <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
              <div style={{ fontSize: '0.825rem', fontWeight: 700, color: '#F9FAFB' }}>
                {currentUser.name}
              </div>
              <div style={{ fontSize: '0.675rem', color: '#9CA3AF' }}>
                {currentUser.role || 'Farmer'} · {currentUser.district || 'Maharashtra'}
              </div>
            </div>

            <button
              type="button"
              onClick={onLogout}
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                color: '#FCA5A5',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                borderRadius: '7px',
                padding: '0.35rem 0.65rem',
                fontSize: '0.725rem',
                fontWeight: 700,
                cursor: 'pointer',
                marginLeft: '0.35rem',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.4)'
                e.currentTarget.style.color = '#FFFFFF'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.2)'
                e.currentTarget.style.color = '#FCA5A5'
              }}
              title="Sign Out of Session"
            >
              Sign Out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
