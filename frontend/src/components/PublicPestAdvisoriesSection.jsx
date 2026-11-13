import { useEffect, useState } from 'react'
import { publicAdvisoriesApi } from '../services/api'

export default function PublicPestAdvisoriesSection() {
  const [advisories, setAdvisories] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filter states
  const [cropFilter, setCropFilter] = useState('')
  const [districtFilter, setDistrictFilter] = useState('')
  const [evidenceFilter, setEvidenceFilter] = useState('')
  const [languageFilter, setLanguageFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  // Translation toggles per advisory id: { [id]: boolean }
  const [showTranslation, setShowTranslation] = useState({})

  // Review modal state
  const [reviewingItem, setReviewingItem] = useState(null)
  const [reviewerId, setReviewerId] = useState('ENTOMOLOGIST-01')
  const [reviewAction, setReviewAction] = useState('APPROVE')
  const [reviewJustification, setReviewJustification] = useState('')
  const [reviewSubmitting, setReviewSubmitting] = useState(false)
  const [reviewMessage, setReviewMessage] = useState(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [listRes, sumRes] = await Promise.all([
        publicAdvisoriesApi.list({
          crop: cropFilter,
          district: districtFilter,
          evidence_type: evidenceFilter,
          language: languageFilter,
          search: searchQuery,
        }),
        publicAdvisoriesApi.summary().catch(() => null),
      ])
      setAdvisories(listRes.advisories || [])
      if (sumRes) setSummary(sumRes)
    } catch (err) {
      setError(err.message || 'Failed to fetch public pest advisories.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [cropFilter, districtFilter, evidenceFilter, languageFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    loadData()
  }

  const toggleTranslation = (id) => {
    setShowTranslation((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const handleOpenReview = (item) => {
    setReviewingItem(item)
    setReviewAction('APPROVE')
    setReviewJustification('Verified against original institutional bulletin.')
    setReviewMessage(null)
  }

  const handleSubmitReview = async (e) => {
    e.preventDefault()
    if (!reviewingItem) return
    setReviewSubmitting(true)
    setReviewMessage(null)
    try {
      const res = await publicAdvisoriesApi.submitReview(reviewingItem.advisory_id, {
        reviewer_id: reviewerId,
        action: reviewAction,
        justification: reviewJustification,
      })
      setReviewMessage({ type: 'success', text: res.message })
      // Update local item
      setAdvisories((prev) =>
        prev.map((a) =>
          a.advisory_id === reviewingItem.advisory_id
            ? { ...a, human_review_status: res.human_review_status, human_reviewer_notes: reviewJustification }
            : a
        )
      )
      setTimeout(() => {
        setReviewingItem(null)
      }, 1200)
    } catch (err) {
      setReviewMessage({ type: 'error', text: err.message || 'Review failed.' })
    } finally {
      setReviewSubmitting(false)
    }
  }

  const getEvidenceBadge = (type) => {
    switch (type) {
      case 'FIELD_SURVEILLANCE_MEASUREMENT':
        return { label: 'Field Measurement', bg: '#0284c7', color: '#ffffff' }
      case 'REPORTED_PEST_SEVERITY':
        return { label: 'Severe Damage Alert', bg: '#dc2626', color: '#ffffff' }
      case 'REPORTED_PEST_ACTIVITY':
        return { label: 'Reported Pest Activity', bg: '#d97706', color: '#ffffff' }
      case 'GENERAL_PREVENTIVE_ADVISORY':
        return { label: 'General Preventive Advisory', bg: '#059669', color: '#ffffff' }
      default:
        return { label: 'Institutional Advisory', bg: '#475569', color: '#ffffff' }
    }
  }

  const getReviewBadge = (status) => {
    switch (status) {
      case 'VERIFIED_ADVISORY':
        return { label: 'Verified by Reviewer', color: '#10b981' }
      case 'REJECTED_EXTRACTION':
        return { label: 'Rejected', color: '#ef4444' }
      case 'PROMOTED_FOR_SURVEILLANCE_CONSIDERATION':
        return { label: 'Flagged for Surveillance Evaluation', color: '#38bdf8' }
      default:
        return { label: 'Pending Human Review', color: '#f59e0b' }
    }
  }

  return (
    <section className="dashboard-section" style={{ padding: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '700', color: '#1e293b', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span>📜</span> Public Pest Advisories & Regional Intelligence
        </h2>
        <p style={{ color: '#64748b', fontSize: '0.95rem', margin: 0 }}>
          Archived and extracted agricultural intelligence bulletins from ICAR-CICR, CROPSAP Maharashtra, Dr. PDKV Akola, and IMD Agromet Services.
        </p>
      </div>

      {/* Critical Scientific Disclaimer */}
      <div style={{
        background: '#fffbeb',
        border: '1px solid #fde68a',
        borderRadius: '8px',
        padding: '1rem',
        marginBottom: '1.5rem',
        display: 'flex',
        gap: '0.75rem',
        alignItems: 'flex-start',
      }}>
        <span style={{ fontSize: '1.25rem', lineHeight: '1.2' }}>ℹ️</span>
        <div style={{ fontSize: '0.85rem', color: '#92400e', lineHeight: '1.5' }}>
          <strong>Critical Scientific Invariant:</strong> Public pest advisories represent institutional recommendations,
          regional warnings, and farmer guidance. They are <strong>NOT verified field-level surveillance measurements</strong>,
          nor are they calibrated machine learning outbreak probabilities. They are presented here as an agricultural
          intelligence layer to assist farmer scouting, completely distinct from the biophysical Environmental Favorability Index.
        </div>
      </div>

      {/* KPI Stats Bar */}
      {summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}>
          <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#0f172a' }}>{summary.total_advisories}</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase' }}>Extracted Entries</div>
          </div>
          <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#059669' }}>{summary.sources_count}</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase' }}>Verified Sources</div>
          </div>
          <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#d97706' }}>
              {summary.evidence_type_counts['GENERAL_PREVENTIVE_ADVISORY'] || 0}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase' }}>Preventive Advisories</div>
          </div>
          <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#dc2626' }}>
              {(summary.evidence_type_counts['REPORTED_PEST_ACTIVITY'] || 0) + (summary.evidence_type_counts['REPORTED_PEST_SEVERITY'] || 0)}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase' }}>Activity & Severity Alerts</div>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', alignItems: 'end' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '0.25rem' }}>Crop</label>
            <select
              value={cropFilter}
              onChange={(e) => setCropFilter(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
            >
              <option value="">All Crops</option>
              <option value="cotton">Cotton (कापूस)</option>
              <option value="soybean">Soybean (सोयाबीन)</option>
              <option value="rice">Rice (भात/धान)</option>
              <option value="maize">Maize (मका)</option>
              <option value="pigeonpea">Pigeonpea (तूर)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '0.25rem' }}>District</label>
            <select
              value={districtFilter}
              onChange={(e) => setDistrictFilter(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
            >
              <option value="">All Districts</option>
              <option value="Nagpur">Nagpur (नागपूर)</option>
              <option value="Amravati">Amravati (अमरावती)</option>
              <option value="Yavatmal">Yavatmal (यवतमाळ)</option>
              <option value="Jalgaon">Jalgaon (जळगाव)</option>
              <option value="Akola">Akola (अकोला)</option>
              <option value="Wardha">Wardha (वर्धा)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '0.25rem' }}>Evidence Classification</label>
            <select
              value={evidenceFilter}
              onChange={(e) => setEvidenceFilter(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
            >
              <option value="">All Classifications</option>
              <option value="GENERAL_PREVENTIVE_ADVISORY">General Preventive Advisory</option>
              <option value="REPORTED_PEST_ACTIVITY">Reported Pest Activity</option>
              <option value="REPORTED_PEST_SEVERITY">Reported Pest Severity</option>
              <option value="FIELD_SURVEILLANCE_MEASUREMENT">Field Surveillance Measurement</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '0.25rem' }}>Language</label>
            <select
              value={languageFilter}
              onChange={(e) => setLanguageFilter(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
            >
              <option value="">All Languages</option>
              <option value="en">English (en)</option>
              <option value="mr">Marathi (मराठी)</option>
              <option value="hi">Hindi (हिंदी)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '0.25rem' }}>Keyword Search</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                placeholder="Search text or pest..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
              />
              <button
                type="submit"
                style={{
                  background: '#0f766e',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '0.5rem 1rem',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '0.9rem',
                }}
              >
                Search
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Advisory Feed */}
      {loading ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading public advisories...</div>
      ) : error ? (
        <div style={{ padding: '1rem', background: '#fee2e2', color: '#b91c1c', borderRadius: '6px' }}>{error}</div>
      ) : advisories.length === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', border: '1px dashed #cbd5e1' }}>
          <p style={{ color: '#64748b', fontSize: '1rem', margin: 0 }}>No public advisories match your selected filters.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {advisories.map((item) => {
            const evBadge = getEvidenceBadge(item.evidence_type)
            const revBadge = getReviewBadge(item.human_review_status)
            const isMrOrHi = item.original_language !== 'en'
            const showingTrans = showTranslation[item.advisory_id]

            return (
              <div
                key={item.advisory_id}
                style={{
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '1.25rem',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.04)',
                }}
              >
                {/* Card Header */}
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <span style={{
                      background: evBadge.bg,
                      color: evBadge.color,
                      fontSize: '0.75rem',
                      fontWeight: '700',
                      padding: '0.25rem 0.6rem',
                      borderRadius: '4px',
                      textTransform: 'uppercase',
                      letterSpacing: '0.02em',
                    }}>
                      {evBadge.label}
                    </span>

                    <span style={{
                      background: '#f1f5f9',
                      color: '#334155',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                    }}>
                      Severity: {item.advisory_severity}
                    </span>

                    <span style={{
                      color: revBadge.color,
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      border: `1px solid ${revBadge.color}40`,
                      background: `${revBadge.color}10`,
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                    }}>
                      {revBadge.label}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: '500' }}>
                    Published: {item.publication_date || 'Undated'}
                  </div>
                </div>

                {/* Organization & Location Meta */}
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ fontWeight: '700', color: '#1e293b', fontSize: '1.05rem' }}>
                    {item.issuing_organization}
                    {item.issuing_office ? ` · ${item.issuing_office}` : ''}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#475569', marginTop: '0.2rem' }}>
                    Source Document: <code>{item.source_document}</code>
                    {item.page_number && ` (p. ${item.page_number})`}
                  </div>
                </div>

                {/* Tags */}
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                  {item.crop && (
                    <span style={{ background: '#ecfdf5', color: '#047857', fontSize: '0.8rem', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: '600' }}>
                      Crop: {item.crop.toUpperCase()}
                    </span>
                  )}
                  {item.pest_common_name && (
                    <span style={{ background: '#fef2f2', color: '#b91c1c', fontSize: '0.8rem', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: '600' }}>
                      Pest: {item.pest_common_name}
                      {item.pest_scientific_name ? ` (${item.pest_scientific_name})` : ''}
                    </span>
                  )}
                  {item.district && (
                    <span style={{ background: '#eff6ff', color: '#1d4ed8', fontSize: '0.8rem', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: '600' }}>
                      District: {item.district}
                    </span>
                  )}
                  <span style={{ background: '#f8fafc', color: '#64748b', fontSize: '0.75rem', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>
                    Lang: {item.original_language.toUpperCase()}
                  </span>
                </div>

                {/* Advisory Text */}
                <div style={{
                  background: '#f8fafc',
                  borderLeft: '4px solid #0f766e',
                  padding: '0.85rem 1rem',
                  borderRadius: '0 6px 6px 0',
                  fontSize: '0.9rem',
                  lineHeight: '1.6',
                  color: '#1e293b',
                  marginBottom: '1rem',
                  fontFamily: isMrOrHi && !showingTrans ? 'system-ui, sans-serif' : 'inherit',
                }}>
                  {showingTrans && item.translated_text ? (
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#0f766e', fontWeight: '700', marginBottom: '0.25rem', textTransform: 'uppercase' }}>
                        English Translation (Dictionary-Assisted):
                      </div>
                      {item.translated_text}
                    </div>
                  ) : (
                    item.advisory_text
                  )}
                </div>

                {/* Translation Toggle for Marathi/Hindi */}
                {isMrOrHi && item.translated_text && (
                  <div style={{ marginBottom: '1rem' }}>
                    <button
                      onClick={() => toggleTranslation(item.advisory_id)}
                      style={{
                        background: 'none',
                        border: '1px solid #cbd5e1',
                        borderRadius: '4px',
                        padding: '0.25rem 0.6rem',
                        fontSize: '0.8rem',
                        color: '#0f766e',
                        cursor: 'pointer',
                        fontWeight: '600',
                      }}
                    >
                      {showingTrans ? '← Show Original Marathi/Hindi Text' : '🌐 View English Summary'}
                    </button>
                  </div>
                )}

                {/* Recommendations Box */}
                {(item.recommended_scouting_actions || item.recommended_management_actions || item.recommended_preventive_actions) && (
                  <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '0.75rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
                    {item.recommended_scouting_actions && (
                      <div style={{ marginBottom: '0.35rem' }}>
                        <strong style={{ color: '#166534' }}>🔍 Scouting Guidance:</strong> {item.recommended_scouting_actions}
                      </div>
                    )}
                    {item.recommended_management_actions && (
                      <div style={{ marginBottom: '0.35rem' }}>
                        <strong style={{ color: '#166534' }}>💊 Management Action:</strong> {item.recommended_management_actions}
                      </div>
                    )}
                    {item.recommended_preventive_actions && (
                      <div>
                        <strong style={{ color: '#166534' }}>🛡️ Preventive Action:</strong> {item.recommended_preventive_actions}
                      </div>
                    )}
                  </div>
                )}

                {/* Reviewer Notes & Action Footer */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid #f1f5f9' }}>
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {item.human_reviewer_notes ? (
                      <span><strong>Reviewer Note:</strong> {item.human_reviewer_notes}</span>
                    ) : (
                      <span>Confidence: {Math.round(item.extraction_confidence * 100)}%</span>
                    )}
                  </div>

                  <button
                    onClick={() => handleOpenReview(item)}
                    style={{
                      background: '#f8fafc',
                      border: '1px solid #cbd5e1',
                      borderRadius: '4px',
                      padding: '0.35rem 0.75rem',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      color: '#334155',
                      cursor: 'pointer',
                    }}
                  >
                    ✍️ Human Review
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Human Review Modal */}
      {reviewingItem && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem',
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: '10px',
            maxWidth: '560px',
            width: '100%',
            padding: '1.5rem',
            boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
          }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.5rem' }}>
              Human Entomological Review
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
              Advisory: <code>{reviewingItem.advisory_id}</code> ({reviewingItem.issuing_organization})
            </p>

            <form onSubmit={handleSubmitReview}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#334155', marginBottom: '0.25rem' }}>
                  Reviewer ID
                </label>
                <input
                  type="text"
                  required
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#334155', marginBottom: '0.25rem' }}>
                  Action
                </label>
                <select
                  value={reviewAction}
                  onChange={(e) => setReviewAction(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                >
                  <option value="APPROVE">APPROVE (Confirm accurate extraction)</option>
                  <option value="REJECT">REJECT (Erroneous or irrelevant content)</option>
                  <option value="CORRECT_FIELDS">CORRECT_FIELDS (Mark as verified with adjustments)</option>
                  {reviewingItem.evidence_type === 'FIELD_SURVEILLANCE_MEASUREMENT' && (
                    <option value="FLAG_FOR_SURVEILLANCE">FLAG_FOR_SURVEILLANCE (Candidate for surveillance evaluation)</option>
                  )}
                </select>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#334155', marginBottom: '0.25rem' }}>
                  Justification / Entomologist Notes
                </label>
                <textarea
                  rows={3}
                  required
                  value={reviewJustification}
                  onChange={(e) => setReviewJustification(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem' }}
                />
              </div>

              {reviewMessage && (
                <div style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  marginBottom: '1rem',
                  fontSize: '0.85rem',
                  background: reviewMessage.type === 'success' ? '#dcfce7' : '#fee2e2',
                  color: reviewMessage.type === 'success' ? '#15803d' : '#b91c1c',
                }}>
                  {reviewMessage.text}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  disabled={reviewSubmitting}
                  onClick={() => setReviewingItem(null)}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    background: '#f8fafc',
                    color: '#475569',
                    fontWeight: '600',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reviewSubmitting}
                  style={{
                    padding: '0.5rem 1.25rem',
                    borderRadius: '6px',
                    border: 'none',
                    background: '#0f766e',
                    color: '#ffffff',
                    fontWeight: '600',
                    cursor: 'pointer',
                  }}
                >
                  {reviewSubmitting ? 'Submitting...' : 'Save Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}

