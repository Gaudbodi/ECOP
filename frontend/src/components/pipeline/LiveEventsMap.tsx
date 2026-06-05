import { useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { X } from 'lucide-react'
import L from 'leaflet'
import { useTheme } from '../../hooks/useTheme'
import { SeverityBadge } from '../ui/SeverityBadge'
import type { CapAlert } from '../../api/types'

/**
 * LiveEventsMap — full-screen overlay showing every currently-dispatched
 * alert as a marker on a Ghana-centred Leaflet map. Each marker carries the
 * matching event-type animation (rain / flood / storm / fire / earthquake /
 * heat / drought / security / default) using the cap-event-* utilities
 * defined in index.css.
 *
 * The component owns its own Leaflet instance — no shared state with the
 * manual entry MapPanel. Rendering inside a `.cap-overlay`-style wrapper
 * keeps the Leaflet controls beneath the modal's chrome.
 */

interface LiveEventsMapProps {
  alerts: CapAlert[]
  open: boolean
  onClose: () => void
}

const TILE_URLS = {
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
}
const TILE_ATTR = '&copy; OpenStreetMap contributors &copy; CARTO'

const EVENT_COLOR: Record<string, string> = {
  rain: '#38bdf8',
  flood: '#0ea5e9',
  storm: '#a78bfa',
  fire: '#f97316',
  earthquake: '#f59e0b',
  heat: '#f97316',
  drought: '#facc15',
  security: '#ef4444',
  alert: '#ef4444',
}

const EVENT_LABEL: Record<string, string> = {
  rain: 'Rain',
  flood: 'Flood',
  storm: 'Storm',
  fire: 'Fire',
  earthquake: 'Earthquake',
  heat: 'Heat',
  drought: 'Drought',
  security: 'Security',
  alert: 'Alert',
}

function classifyEvent(alert: CapAlert): string {
  const text = `${alert.event || ''} ${alert.headline || ''} ${alert.description || ''}`.toLowerCase()
  for (const kw of ['flood', 'rain', 'storm', 'fire', 'earthquake', 'drought', 'heat', 'cholera', 'security']) {
    if (text.includes(kw)) return kw === 'cholera' ? 'security' : kw
  }
  return 'alert'
}

function radiusKmFor(alert: CapAlert): number {
  // Heuristic — generators today don't always pass radius. Defaults derived
  // from severity so the visual is informative without faking precision.
  const s = (alert.severity || '').toLowerCase()
  if (s === 'extreme') return 25
  if (s === 'severe') return 15
  if (s === 'moderate') return 8
  return 5
}

export function LiveEventsMap({ alerts, open, onClose }: LiveEventsMapProps) {
  const { theme } = useTheme()
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const tileRef = useRef<L.TileLayer | null>(null)
  const layersRef = useRef<L.LayerGroup | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  // Filter to currently dispatched, NOT terminated, with valid coords.
  const live = useMemo(
    () =>
      alerts
        .filter((a) => a.workflow_stage === 3 && a.lifecycle !== 'terminated')
        .map((a) => ({
          alert: a,
          eventType: classifyEvent(a),
          extended: a.lifecycle === 'extended',
          lat: a.geo?.lat,
          lon: a.geo?.lon,
        }))
        .filter((x) => Number.isFinite(x.lat) && Number.isFinite(x.lon)),
    [alerts],
  )

  // Group by event type for the legend.
  const counts = useMemo(() => {
    const m: Record<string, number> = {}
    for (const ev of live) m[ev.eventType] = (m[ev.eventType] || 0) + 1
    return m
  }, [live])

  // Init / teardown the Leaflet map on open/close. Tracked via `mapReady`
  // so the marker-rendering effect re-runs the moment the map exists —
  // the previous version had a referentially-stable `live` array that
  // never triggered re-render after the first open cycle.
  const [mapReady, setMapReady] = useState(false)
  useEffect(() => {
    if (!open || !containerRef.current || mapRef.current) return
    const map = L.map(containerRef.current, { zoomControl: true }).setView([7.95, -1.02], 6.7)
    mapRef.current = map
    tileRef.current = L.tileLayer(TILE_URLS[theme], { attribution: TILE_ATTR }).addTo(map)
    layersRef.current = L.layerGroup().addTo(map)
    const t = window.setTimeout(() => map.invalidateSize(), 120)
    setMapReady(true)
    return () => {
      window.clearTimeout(t)
      map.remove()
      mapRef.current = null
      tileRef.current = null
      layersRef.current = null
      setMapReady(false)
    }
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps

  // Theme-reactive tiles
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (tileRef.current) map.removeLayer(tileRef.current)
    tileRef.current = L.tileLayer(TILE_URLS[theme], { attribution: TILE_ATTR }).addTo(map)
  }, [theme])

  // Render markers each time the live list changes.
  useEffect(() => {
    const layers = layersRef.current
    const map = mapRef.current
    if (!layers || !map) return
    layers.clearLayers()
    if (live.length === 0) return

    const bounds = L.latLngBounds([])
    for (const { alert, eventType, extended, lat, lon } of live) {
      const color = EVENT_COLOR[eventType] ?? EVENT_COLOR.alert
      const radius = radiusKmFor(alert)
      // Extended alerts get a thicker outline + higher fill opacity so the
      // worsening situation reads at a glance on the operational map.
      const circle = L.circle([lat as number, lon as number], {
        radius: radius * 1000,
        color,
        weight: extended ? 3 : 1.5,
        opacity: extended ? 1 : 0.85,
        fillColor: color,
        fillOpacity: extended ? 0.3 : 0.18,
        className: `cap-event-circle cap-event-${eventType}${extended ? ' cap-extended' : ''}`,
      })
      const pinClass = extended ? 'cap-target-pin cap-target-pin--extended' : 'cap-target-pin'
      const marker = L.marker([lat as number, lon as number], {
        icon: L.divIcon({
          className: pinClass,
          html: `<div class="cap-target-pin__inner" style="--c:${color}"></div>`,
          iconSize: extended ? [28, 28] : [22, 22],
          iconAnchor: extended ? [14, 14] : [11, 11],
        }),
      }).bindTooltip(
        `<strong>${alert.headline}</strong><br/>${EVENT_LABEL[eventType] ?? 'Alert'} · ${alert.severity}${extended ? ' · ⬆ EXTENDED' : ''}`,
        { direction: 'top' },
      )
      marker.on('click', () => setSelected(alert.identifier))
      layers.addLayer(circle)
      layers.addLayer(marker)
      bounds.extend([lat as number, lon as number])
    }
    if (bounds.isValid()) map.flyToBounds(bounds.pad(0.3), { duration: 0.6, maxZoom: 9 })
  }, [live, mapReady])

  // Close on Esc
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  const selectedAlert = selected ? live.find((x) => x.alert.identifier === selected) : null

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="live-events-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="cap-live-events fixed inset-0 bg-slate-950/85 backdrop-blur-md p-4 sm:p-6 flex flex-col"
          onClick={onClose}
        >
          <motion.div
            initial={{ y: 16, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 16, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="glass-card flex-1 flex flex-col p-4 sm:p-6 max-w-[1400px] w-full mx-auto"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="live-events-title"
          >
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <p className="text-xs font-mono uppercase tracking-[0.22em] text-sky-300/80 mb-1">
                  Operational view
                </p>
                <h2 id="live-events-title" className="text-2xl sm:text-3xl font-bold leading-tight">
                  Live events · Ghana
                </h2>
                <p className="text-sm text-white/60 mt-1">
                  {live.length} dispatched event{live.length === 1 ? '' : 's'} ongoing.
                  Click a marker for detail.
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="w-9 h-9 rounded-full border border-white/15 bg-white/5 flex items-center justify-center hover:bg-white/10"
                aria-label="Close live events map"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Legend chips */}
            <div className="flex flex-wrap gap-2 mb-3 text-xs">
              {Object.entries(counts).map(([type, n]) => (
                <span
                  key={type}
                  className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md border bg-white/5"
                  style={{ borderColor: (EVENT_COLOR[type] ?? '#fff') + '55' }}
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{
                      background: EVENT_COLOR[type] ?? '#fff',
                      boxShadow: `0 0 10px 2px ${EVENT_COLOR[type] ?? '#fff'}`,
                    }}
                  />
                  <span className="font-mono">{EVENT_LABEL[type] ?? type}</span>
                  <span className="font-bold tabular-nums">{n}</span>
                </span>
              ))}
              {live.length === 0 && (
                <span className="text-white/55">No dispatched alerts with map coordinates.</span>
              )}
            </div>

            <div className="relative flex-1 min-h-[400px]">
              <div
                ref={containerRef}
                className="w-full h-full rounded-2xl overflow-hidden border border-white/10"
              />

              {/* Event-type animation overlays — one absolutely-positioned div
                  per active type, sitting above the tiles but below the
                  Leaflet controls. The animations are CSS-driven from
                  index.css's cap-event-* utilities. */}
              {Object.keys(counts).map((type) => (
                <div
                  key={type}
                  aria-hidden="true"
                  className={`pointer-events-none absolute inset-0 rounded-2xl cap-event-overlay cap-event-${type}`}
                  style={{ opacity: 0.32 }}
                />
              ))}

              {/* Selected marker detail card */}
              {selectedAlert && (
                <motion.div
                  initial={{ y: 8, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: 8, opacity: 0 }}
                  className="absolute left-4 bottom-4 max-w-md glass-card !p-4 pointer-events-auto"
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-sky-300/80">
                      {selectedAlert.alert.identifier}
                    </p>
                    <SeverityBadge severity={selectedAlert.alert.severity} />
                  </div>
                  <h3 className="text-base font-semibold leading-snug">
                    {selectedAlert.alert.headline}
                  </h3>
                  <div className="text-xs text-white/55 mt-1 font-mono">
                    {selectedAlert.alert.sent}
                  </div>
                  <p className="text-sm text-white/75 mt-2 line-clamp-3">
                    {selectedAlert.alert.description}
                  </p>
                  <div className="flex items-center gap-2 mt-2 text-[11px]">
                    <span
                      className="px-1.5 py-0.5 rounded-md font-mono"
                      style={{
                        background: (EVENT_COLOR[selectedAlert.eventType] ?? '#fff') + '22',
                        color: EVENT_COLOR[selectedAlert.eventType] ?? '#fff',
                      }}
                    >
                      {EVENT_LABEL[selectedAlert.eventType] ?? 'Alert'}
                    </span>
                    <span className="text-white/55">
                      {selectedAlert.alert.affected_regions?.join(', ') || 'Ghana (General)'}
                    </span>
                    <button
                      type="button"
                      onClick={() => setSelected(null)}
                      className="ml-auto text-white/50 hover:text-white"
                    >
                      dismiss
                    </button>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
