import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = ''

const defaultForm = {
  type: 'flooding',
  title: 'Flooding near Central Avenue',
  description: 'Heavy rain has caused surface water to pool near the central corridor and traffic lanes are obstructed.',
  source: 'citizen',
  latitude: 40.7128,
  longitude: -74.006,
  severity: 4,
  confidence: 0.88,
}

const incidentTypes = ['flooding', 'power_outage', 'road_blockage', 'fire', 'medical_emergency', 'traffic_accident']
const statusOptions = ['reported', 'analyzing', 'active', 'assigned', 'in_progress', 'resolved']
const cityDistricts = [
  { name: 'Downtown', left: 24, top: 28, width: 30, height: 22 },
  { name: 'Harbor', left: 58, top: 18, width: 25, height: 20 },
  { name: 'Northside', left: 20, top: 60, width: 28, height: 24 },
  { name: 'Riverside', left: 52, top: 52, width: 30, height: 26 },
]

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json().catch(() => ({}))
    : await response.text().catch(() => '')

  if (!response.ok) {
    throw new Error(payload?.detail || payload?.message || `Request failed (${response.status})`)
  }

  return payload
}

function formatStatus(value) {
  if (!value) return 'Unassigned'
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function buildStatusTimeline(currentStatus) {
  const steps = ['reported', 'analyzing', 'active', 'assigned', 'in_progress', 'resolved']
  const activeIndex = Math.max(0, steps.indexOf(currentStatus) ?? 0)

  return steps.map((step, index) => ({
    label: formatStatus(step),
    complete: index <= activeIndex,
    current: step === currentStatus,
  }))
}

function App() {
  const [summary, setSummary] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [selectedIncidentId, setSelectedIncidentId] = useState('')
  const [incidentImpact, setIncidentImpact] = useState(null)
  const [incidentResponse, setIncidentResponse] = useState(null)
  const [dashboardMap, setDashboardMap] = useState({ entities: [], incidents: [] })
  const [formData, setFormData] = useState(defaultForm)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [statusUpdating, setStatusUpdating] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [noteText, setNoteText] = useState('')
  const [noteSubmitting, setNoteSubmitting] = useState(false)
  const [assignmentForm, setAssignmentForm] = useState({ department: 'Utilities', escalation_level: 2, note: '' })
  const [assignmentSubmitting, setAssignmentSubmitting] = useState(false)
  const [simulationSubmitting, setSimulationSubmitting] = useState(false)
  const [incidentTimeline, setIncidentTimeline] = useState({ sla_minutes: 0, timeline: [] })

  const selectedIncident = incidents.find((incident) => incident.id === selectedIncidentId) || incidents[0] || null

  const filteredIncidents = incidents.filter((incident) => {
    const matchesStatus = statusFilter === 'all' || incident.status === statusFilter
    const haystack = `${incident.title} ${incident.type} ${incident.description}`.toLowerCase()
    const matchesSearch = haystack.includes(searchTerm.toLowerCase())
    return matchesStatus && matchesSearch
  })

  const visibleSelectedIncident = filteredIncidents.find((incident) => incident.id === selectedIncidentId) || filteredIncidents[0] || null

  const loadDashboard = async (preferredIncidentId = null) => {
    try {
      const [summaryData, incidentsData, mapData] = await Promise.all([
        apiRequest('/api/dashboard/summary'),
        apiRequest('/api/dashboard/incidents'),
        apiRequest('/api/dashboard/map'),
      ])

      setSummary(summaryData)
      setIncidents(incidentsData)
      setDashboardMap(mapData)

      if (incidentsData.length > 0) {
        if (preferredIncidentId && incidentsData.some((incident) => incident.id === preferredIncidentId)) {
          setSelectedIncidentId(preferredIncidentId)
        } else {
          setSelectedIncidentId((current) =>
            current && incidentsData.some((incident) => incident.id === current)
              ? current
              : incidentsData[0].id,
          )
        }
      } else {
        setSelectedIncidentId('')
      }

      return incidentsData
    } catch (loadError) {
      setError(loadError.message)
      return []
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()

    const interval = window.setInterval(() => {
      loadDashboard(selectedIncidentId)
    }, 15000)

    return () => window.clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!visibleSelectedIncident) {
      setIncidentImpact(null)
      setIncidentResponse(null)
      return
    }

    let isMounted = true

    const loadIncidentDetails = async () => {
      try {
        const [impactData, responseData, timelineData] = await Promise.all([
          apiRequest(`/api/incidents/${visibleSelectedIncident.id}/impact`),
          apiRequest(`/api/incidents/${visibleSelectedIncident.id}/response`),
          apiRequest(`/api/incidents/${visibleSelectedIncident.id}/timeline`),
        ])

        if (isMounted) {
          setIncidentImpact(impactData)
          setIncidentResponse(responseData)
          setIncidentTimeline(timelineData)
        }
      } catch (detailError) {
        if (isMounted) {
          setError(detailError.message)
        }
      }
    }

    loadIncidentDetails()

    return () => {
      isMounted = false
    }
  }, [visibleSelectedIncident])

  const handleFieldChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({
      ...current,
      [name]: name === 'severity' || name === 'confidence' || name === 'latitude' || name === 'longitude'
        ? Number(value)
        : value,
    }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')

    try {
      const created = await apiRequest('/api/incidents', {
        method: 'POST',
        body: JSON.stringify(formData),
      })

      await apiRequest(`/api/incidents/${created.id}/analyze`, { method: 'POST' })
      setFormData(defaultForm)
      await loadDashboard(created.id)
    } catch (submitError) {
      setError(submitError.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleStatusChange = async (event) => {
    if (!visibleSelectedIncident) return

    const nextStatus = event.target.value
    setStatusUpdating(true)
    setError('')

    try {
      await apiRequest(`/api/incidents/${visibleSelectedIncident.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: nextStatus }),
      })
      await loadDashboard(visibleSelectedIncident.id)
    } catch (statusError) {
      setError(statusError.message)
    } finally {
      setStatusUpdating(false)
    }
  }

  const handleWorkflowAction = async (targetStatus) => {
    if (!visibleSelectedIncident) return

    setStatusUpdating(true)
    setError('')

    try {
      await apiRequest(`/api/incidents/${visibleSelectedIncident.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: targetStatus }),
      })
      await loadDashboard(visibleSelectedIncident.id)
    } catch (statusError) {
      setError(statusError.message)
    } finally {
      setStatusUpdating(false)
    }
  }

  const handleAddNote = async (event) => {
    event.preventDefault()
    if (!visibleSelectedIncident || !noteText.trim()) return

    setNoteSubmitting(true)
    setError('')

    try {
      await apiRequest(`/api/incidents/${visibleSelectedIncident.id}/notes`, {
        method: 'POST',
        body: JSON.stringify({ text: noteText.trim() }),
      })
      setNoteText('')
      await loadDashboard(visibleSelectedIncident.id)
    } catch (noteError) {
      setError(noteError.message)
    } finally {
      setNoteSubmitting(false)
    }
  }

  const handleAssignIncident = async (event) => {
    event.preventDefault()
    if (!visibleSelectedIncident) return

    setAssignmentSubmitting(true)
    setError('')

    try {
      await apiRequest(`/api/incidents/${visibleSelectedIncident.id}/assign`, {
        method: 'POST',
        body: JSON.stringify({
          department: assignmentForm.department,
          escalation_level: Number(assignmentForm.escalation_level),
          note: assignmentForm.note.trim() || undefined,
        }),
      })
      setAssignmentForm((current) => ({ ...current, note: '' }))
      await loadDashboard(visibleSelectedIncident.id)
    } catch (assignError) {
      setError(assignError.message)
    } finally {
      setAssignmentSubmitting(false)
    }
  }

  const handleSimulation = async () => {
    if (!visibleSelectedIncident) return

    setSimulationSubmitting(true)
    setError('')

    try {
      await apiRequest(`/api/incidents/${visibleSelectedIncident.id}/simulate`, {
        method: 'POST',
        body: JSON.stringify({ scenario: 'grid_failure' }),
      })
      await loadDashboard(visibleSelectedIncident.id)
    } catch (simulateError) {
      setError(simulateError.message)
    } finally {
      setSimulationSubmitting(false)
    }
  }

  const mapMarkers = dashboardMap.incidents || []
  const incidentPriorityCount = incidents.filter((incident) => incident.severity >= 4).length
  const statusTimeline = visibleSelectedIncident ? buildStatusTimeline(visibleSelectedIncident.status) : []

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI City OS</p>
          <h1>City operations command center</h1>
        </div>
        <button className="ghost-button" type="button" onClick={loadDashboard}>
          Refresh
        </button>
      </header>

      {error && <div className="banner error">{error}</div>}

      <section className="stats-grid">
        <article className="stat-card primary">
          <span>Active incidents</span>
          <strong>{summary?.total_active_incidents ?? 0}</strong>
          <small>{summary?.critical_incidents ?? 0} critical</small>
        </article>
        <article className="stat-card">
          <span>Affected services</span>
          <strong>{summary?.affected_services ?? 0}</strong>
          <small>Critical infrastructure</small>
        </article>
        <article className="stat-card">
          <span>Estimated impact</span>
          <strong>{summary?.estimated_affected_population ?? 0}</strong>
          <small>People affected</small>
        </article>
        <article className="stat-card">
          <span>High risk</span>
          <strong>{incidentPriorityCount}</strong>
          <small>Severity 4+ incidents</small>
        </article>
      </section>

      <main className="content-grid">
        <section className="panel panel-large">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Urban map</p>
              <h2>City signal view</h2>
            </div>
          </div>

          <div className="city-map">
            <div className="map-grid" />
            <div className="map-river" />
            <div className="road road-horizontal road-a" />
            <div className="road road-horizontal road-b" />
            <div className="road road-vertical road-c" />
            <div className="road road-vertical road-d" />

            {cityDistricts.map((district) => (
              <div
                key={district.name}
                className="district-block"
                style={{ left: `${district.left}%`, top: `${district.top}%`, width: `${district.width}%`, height: `${district.height}%` }}
              >
                <span>{district.name}</span>
              </div>
            ))}

            {dashboardMap.entities?.slice(0, 40).map((entity) => {
              const left = Math.max(4, Math.min(96, ((Number(entity.longitude) + 180) / 360) * 100))
              const top = Math.max(4, Math.min(96, ((90 - Number(entity.latitude)) / 180) * 100))

              return (
                <span
                  key={entity.id}
                  className={`entity-dot ${entity.type}`}
                  style={{ left: `${left}%`, top: `${top}%` }}
                  title={`${entity.name} · ${entity.type}`}
                />
              )
            })}

            {mapMarkers.map((incident) => {
              const left = Math.max(6, Math.min(94, ((Number(incident.longitude) + 180) / 360) * 100))
              const top = Math.max(6, Math.min(94, ((90 - Number(incident.latitude)) / 180) * 100))

              return (
                <button
                  key={incident.id}
                  type="button"
                  className={`incident-pin severity-${incident.severity}`}
                  style={{ left: `${left}%`, top: `${top}%` }}
                  onClick={() => setSelectedIncidentId(incident.id)}
                  title={`${incident.title} (${incident.severity}/5)`}
                >
                  {incident.severity}
                </button>
              )
            })}
          </div>
        </section>

        <aside className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Dispatch</p>
              <h2>New incident</h2>
            </div>
          </div>

          <form className="incident-form" onSubmit={handleSubmit}>
            <label>
              Incident type
              <select name="type" value={formData.type} onChange={handleFieldChange}>
                {incidentTypes.map((type) => (
                  <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </label>

            <label>
              Title
              <input name="title" value={formData.title} onChange={handleFieldChange} required />
            </label>

            <label>
              Description
              <textarea name="description" value={formData.description} onChange={handleFieldChange} rows="4" required />
            </label>

            <div className="inline-fields">
              <label>
                Source
                <select name="source" value={formData.source} onChange={handleFieldChange}>
                  <option value="citizen">Citizen</option>
                  <option value="sensor">Sensor</option>
                  <option value="camera">Camera</option>
                  <option value="government">Government</option>
                  <option value="system">System</option>
                </select>
              </label>

              <label>
                Severity
                <input name="severity" type="number" min="1" max="5" value={formData.severity} onChange={handleFieldChange} />
              </label>
            </div>

            <div className="inline-fields">
              <label>
                Latitude
                <input name="latitude" type="number" step="0.0001" value={formData.latitude} onChange={handleFieldChange} />
              </label>
              <label>
                Longitude
                <input name="longitude" type="number" step="0.0001" value={formData.longitude} onChange={handleFieldChange} />
              </label>
            </div>

            <label>
              Confidence
              <input name="confidence" type="number" min="0" max="1" step="0.01" value={formData.confidence} onChange={handleFieldChange} />
            </label>

            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? 'Sending...' : 'Submit incident'}
            </button>
          </form>
        </aside>
      </main>

      <section className="lower-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Live queue</p>
              <h2>Incidents</h2>
            </div>
          </div>

          <div className="queue-tools">
            <input
              className="search-box"
              type="search"
              value={searchTerm}
              placeholder="Search incidents…"
              onChange={(event) => setSearchTerm(event.target.value)}
            />
            <div className="status-filters">
              <button
                type="button"
                className={`filter-chip ${statusFilter === 'all' ? 'active' : ''}`}
                onClick={() => setStatusFilter('all')}
              >
                All
              </button>
              {statusOptions.map((status) => (
                <button
                  key={status}
                  type="button"
                  className={`filter-chip ${statusFilter === status ? 'active' : ''}`}
                  onClick={() => setStatusFilter(status)}
                >
                  {formatStatus(status)}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <p className="muted">Loading incidents…</p>
          ) : (
            <div className="incident-list">
              {filteredIncidents.length === 0 ? (
                <p className="muted">No incidents match the current filters.</p>
              ) : (
                filteredIncidents.map((incident) => (
                  <button
                    key={incident.id}
                    type="button"
                    className={`incident-card ${incident.id === visibleSelectedIncident?.id ? 'selected' : ''}`}
                    onClick={() => setSelectedIncidentId(incident.id)}
                  >
                    <div className="incident-topline">
                      <span className={`severity-badge severity-${incident.severity}`}>{incident.severity}/5</span>
                      <span className="status-pill">{formatStatus(incident.status)}</span>
                    </div>
                    <strong>{incident.title}</strong>
                    <small>{incident.type}</small>
                  </button>
                ))
              )}
            </div>
          )}
        </section>

        <section className="panel detail-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Analysis</p>
              <h2>{visibleSelectedIncident?.title || 'No incident selected'}</h2>
            </div>
          </div>

          {visibleSelectedIncident ? (
            <>
              <div className="detail-meta">
                <span>{visibleSelectedIncident.type}</span>
                <span>{formatStatus(visibleSelectedIncident.status)}</span>
                <span>{visibleSelectedIncident.source}</span>
              </div>

              <div className="status-row">
                <label className="status-select-wrap">
                  Update status
                  <select value={visibleSelectedIncident.status} onChange={handleStatusChange} disabled={statusUpdating}>
                    {statusOptions.map((status) => (
                      <option key={status} value={status}>{formatStatus(status)}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="workflow-actions">
                <button type="button" className="workflow-button" onClick={() => handleWorkflowAction('analyzing')}>
                  Acknowledge
                </button>
                <button type="button" className="workflow-button primary" onClick={() => handleWorkflowAction('assigned')}>
                  Dispatch
                </button>
                <button type="button" className="workflow-button success" onClick={() => handleWorkflowAction('resolved')}>
                  Resolve
                </button>
              </div>

              <p className="detail-copy">{visibleSelectedIncident.description}</p>

              <div className="response-summary">
                <div>
                  <span>Response department</span>
                  <strong>{incidentResponse?.department || visibleSelectedIncident.assigned_department || 'Awaiting assignment'}</strong>
                </div>
                <div>
                  <span>Urgency</span>
                  <strong>{incidentResponse?.urgency || 'Pending'}</strong>
                </div>
                <div>
                  <span>Priority</span>
                  <strong>{incidentResponse?.priority || 'Monitoring'}</strong>
                </div>
                <div>
                  <span>SLA</span>
                  <strong>{incidentTimeline?.sla_minutes ?? 0} min</strong>
                </div>
              </div>

              <div className="timeline">
                {statusTimeline.map((step) => (
                  <div key={step.label} className={`timeline-item ${step.complete ? 'complete' : ''} ${step.current ? 'current' : ''}`}>
                    <span className="timeline-dot" />
                    <span>{step.label}</span>
                  </div>
                ))}
              </div>

              <div className="impact-grid">
                <div className="mini-card">
                  <span>Severity</span>
                  <strong>{visibleSelectedIncident.severity}/5</strong>
                </div>
                <div className="mini-card">
                  <span>Confidence</span>
                  <strong>{visibleSelectedIncident.confidence ? `${visibleSelectedIncident.confidence.toFixed(2)}` : '0.00'}</strong>
                </div>
                <div className="mini-card">
                  <span>Latitude</span>
                  <strong>{visibleSelectedIncident.latitude}</strong>
                </div>
                <div className="mini-card">
                  <span>Longitude</span>
                  <strong>{visibleSelectedIncident.longitude}</strong>
                </div>
              </div>

              {incidentImpact && (
                <div className="insight-box">
                  <h3>Impact analysis</h3>
                  <ul>
                    <li>Directly affected: {incidentImpact.directly_affected?.join(', ') || 'None'}</li>
                    <li>Secondarily affected: {incidentImpact.secondarily_affected?.join(', ') || 'None'}</li>
                    <li>Critical services: {incidentImpact.critical_services_affected?.join(', ') || 'None'}</li>
                    <li>Estimated population: {incidentImpact.estimated_population}</li>
                    <li>Impact level: {incidentImpact.impact_level}</li>
                  </ul>
                </div>
              )}

              {incidentResponse && (
                <div className="insight-box response-box">
                  <h3>Response center</h3>
                  <div className="response-metrics">
                    <span><strong>Priority:</strong> {incidentResponse.priority}</span>
                    <span><strong>Urgency:</strong> {incidentResponse.estimated_urgency || incidentResponse.urgency}</span>
                    <span><strong>Departments:</strong> {(incidentResponse.responsible_departments || []).join(', ') || 'Unassigned'}</span>
                  </div>

                  <p className="response-summary-copy">{incidentResponse.response_summary || 'No summary available yet.'}</p>

                  <div className="task-list">
                    {(incidentResponse.tasks || []).map((task) => (
                      <div key={`${task.department}-${task.action}`} className="task-item">
                        <div className="task-header">
                          <span className="task-department">{task.department}</span>
                          <span className={`task-priority ${task.priority?.toLowerCase() || 'medium'}`}>{task.priority}</span>
                        </div>
                        <p>{task.action}</p>
                        <small>{task.status}</small>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="insight-box note-box">
                <h3>Dispatch assignment</h3>
                <form className="assignment-form" onSubmit={handleAssignIncident}>
                  <label>
                    Department
                    <select
                      value={assignmentForm.department}
                      onChange={(event) => setAssignmentForm((current) => ({ ...current, department: event.target.value }))}
                    >
                      <option value="Utilities">Utilities</option>
                      <option value="Traffic Control">Traffic Control</option>
                      <option value="Public Works">Public Works</option>
                      <option value="Emergency Services">Emergency Services</option>
                      <option value="Hospital Administration">Hospital Administration</option>
                    </select>
                  </label>

                  <label>
                    Escalation level
                    <input
                      type="number"
                      min="1"
                      max="5"
                      value={assignmentForm.escalation_level}
                      onChange={(event) => setAssignmentForm((current) => ({ ...current, escalation_level: Number(event.target.value) }))}
                    />
                  </label>

                  <textarea
                    value={assignmentForm.note}
                    onChange={(event) => setAssignmentForm((current) => ({ ...current, note: event.target.value }))}
                    rows="3"
                    placeholder="Describe dispatch context or escalation reason"
                  />

                  <button type="submit" className="primary-button" disabled={assignmentSubmitting}>
                    {assignmentSubmitting ? 'Assigning…' : 'Assign incident'}
                  </button>
                </form>
              </div>

              <div className="insight-box note-box">
                <h3>Service dependency simulation</h3>
                <button type="button" className="primary-button" onClick={handleSimulation} disabled={simulationSubmitting}>
                  {simulationSubmitting ? 'Running simulation…' : 'Run dependency simulation'}
                </button>

                {(visibleSelectedIncident.service_dependencies || []).length > 0 && (
                  <ul className="note-list">
                    {(visibleSelectedIncident.service_dependencies || []).map((dependency) => (
                      <li key={dependency}>{dependency}</li>
                    ))}
                  </ul>
                )}

                {(visibleSelectedIncident.simulation_history || []).length > 0 && (
                  <div className="timeline-block">
                    {visibleSelectedIncident.simulation_history.slice().reverse().map((event, index) => (
                      <div key={`${event.type}-${index}`} className="mini-timeline-item">
                        <span>{event.scenario}</span>
                        <small>{new Date(event.timestamp).toLocaleString()}</small>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="insight-box note-box">
                <h3>Operator notes</h3>
                <form className="note-form" onSubmit={handleAddNote}>
                  <textarea
                    value={noteText}
                    onChange={(event) => setNoteText(event.target.value)}
                    rows="3"
                    placeholder="Add an update for the response team"
                  />
                  <button type="submit" className="primary-button" disabled={noteSubmitting || !noteText.trim()}>
                    {noteSubmitting ? 'Saving…' : 'Add note'}
                  </button>
                </form>

                <ul className="note-list">
                  {(visibleSelectedIncident.notes || []).length === 0 ? (
                    <li className="muted">No notes yet.</li>
                  ) : (
                    (visibleSelectedIncident.notes || []).slice().reverse().map((note, index) => (
                      <li key={`${note}-${index}`}>{note}</li>
                    ))
                  )}
                </ul>
              </div>
            </>
          ) : (
            <p className="muted">Create an incident to begin monitoring the city response.</p>
          )}
        </section>
      </section>
    </div>
  )
}

export default App
