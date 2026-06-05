import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet-draw'
import { useTheme } from '../../hooks/useTheme'

/**
 * MapPanel — raw Leaflet wrapper.
 *
 * Two modes the manual-entry flow drives:
 *   1. Pick mode      — operator clicks the map to drop a marker (no target).
 *   2. Resolved mode  — `target` is set; the map flies to (lat, lon), draws a
 *                       radius circle, and overlays an alert-type animation
 *                       (rain / storm / fire pulses).
 *
 * The animation is purely CSS — a positioned overlay <div> inside the same
 * container, locked to the circle's bounds. Phase 5 will swap Leaflet for
 * Mapbox; the prop contract { target, onLocationChange } stays stable.
 */

export interface MapTarget {
  lat: number
  lon: number
  radius_km: number
  label: string
  event_type: string  // 'rain' | 'storm' | 'fire' | 'flood' | 'alert' (default)
}

interface MapPanelProps {
  onLocationChange: (lat: number, lon: number) => void
  visible: boolean
  className?: string
  /** When set, the map flies to this point and draws a radius circle. */
  target?: MapTarget | null
  /** Confirmation/preview maps disable interactive draw + ignore clicks. */
  readonly?: boolean
}

const TILE_URLS = {
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
}
const TILE_ATTRIBUTION = '&copy; OpenStreetMap contributors &copy; CARTO'

const EVENT_COLORS: Record<string, string> = {
  rain: '#38bdf8',
  storm: '#a78bfa',
  flood: '#0ea5e9',
  fire: '#f97316',
  earthquake: '#f59e0b',
  drought: '#facc15',
  heat: '#f97316',
  alert: '#ef4444',
}

export function MapPanel({
  onLocationChange,
  visible,
  className,
  target,
  readonly = false,
}: MapPanelProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const tileRef = useRef<L.TileLayer | null>(null)
  const drawnItemsRef = useRef<L.FeatureGroup | null>(null)
  const targetMarkerRef = useRef<L.Marker | null>(null)
  const targetCircleRef = useRef<L.Circle | null>(null)
  const overlayRef = useRef<HTMLDivElement | null>(null)

  const onLocationChangeRef = useRef(onLocationChange)
  useEffect(() => {
    onLocationChangeRef.current = onLocationChange
  }, [onLocationChange])

  const { theme } = useTheme()

  // 1. Init once on mount.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = L.map(containerRef.current, {
      zoomControl: !readonly,
      dragging: !readonly,
      scrollWheelZoom: !readonly,
      doubleClickZoom: !readonly,
      touchZoom: !readonly,
      boxZoom: !readonly,
      keyboard: !readonly,
    }).setView([7.9465, -1.0232], 6.5)
    mapRef.current = map

    const tile = L.tileLayer(TILE_URLS[theme], {
      attribution: TILE_ATTRIBUTION,
    }).addTo(map)
    tileRef.current = tile

    if (!readonly) {
      const drawnItems = new L.FeatureGroup()
      map.addLayer(drawnItems)
      drawnItemsRef.current = drawnItems

      const drawControl = new (L.Control as unknown as {
        Draw: new (opts: unknown) => L.Control
      }).Draw({
        draw: { polyline: false, circlemarker: false },
        edit: { featureGroup: drawnItems },
      })
      map.addControl(drawControl)

      map.on(
        (L as unknown as { Draw: { Event: { CREATED: string } } }).Draw.Event.CREATED,
        (e: L.LeafletEvent) => {
          const evt = e as L.LeafletEvent & { layer: L.Layer }
          drawnItems.clearLayers()
          drawnItems.addLayer(evt.layer)
          const layer = evt.layer as L.Marker | L.Polygon | L.Rectangle | L.Circle
          const ll: L.LatLng =
            'getLatLng' in layer && typeof layer.getLatLng === 'function'
              ? (layer as L.Marker | L.Circle).getLatLng()
              : (layer as L.Polygon | L.Rectangle).getBounds().getCenter()
          onLocationChangeRef.current(ll.lat, ll.lng)
        },
      )
    }

    return () => {
      map.remove()
      mapRef.current = null
      tileRef.current = null
      drawnItemsRef.current = null
      targetMarkerRef.current = null
      targetCircleRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 2. Theme-reactive tile swap.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (tileRef.current) map.removeLayer(tileRef.current)
    tileRef.current = L.tileLayer(TILE_URLS[theme], { attribution: TILE_ATTRIBUTION }).addTo(map)
  }, [theme])

  // 3. invalidateSize when visible toggles.
  useEffect(() => {
    if (visible && mapRef.current) {
      const id = window.setTimeout(() => mapRef.current?.invalidateSize(), 100)
      return () => window.clearTimeout(id)
    }
  }, [visible])

  // 4. Render / update target circle + flyTo.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    // Clear previous target
    if (targetCircleRef.current) {
      map.removeLayer(targetCircleRef.current)
      targetCircleRef.current = null
    }
    if (targetMarkerRef.current) {
      map.removeLayer(targetMarkerRef.current)
      targetMarkerRef.current = null
    }

    if (!target) return

    const color = EVENT_COLORS[target.event_type] ?? EVENT_COLORS.alert
    const circle = L.circle([target.lat, target.lon], {
      radius: target.radius_km * 1000,
      color,
      weight: 2,
      fillColor: color,
      fillOpacity: 0.12,
    }).addTo(map)
    targetCircleRef.current = circle

    const marker = L.marker([target.lat, target.lon], {
      icon: L.divIcon({
        className: 'cap-target-pin',
        html: `<div class="cap-target-pin__inner" style="--c:${color}"></div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      }),
    })
      .bindTooltip(`${target.label} · ${target.radius_km} km`, {
        permanent: false,
        direction: 'top',
      })
      .addTo(map)
    targetMarkerRef.current = marker

    // Fit to the circle's bounds with a touch of padding for a clear zoom-in.
    map.flyToBounds(circle.getBounds().pad(0.4), { duration: 0.9, maxZoom: 12 })
  }, [target])

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className={
          className ?? 'w-full h-[420px] rounded-2xl overflow-hidden border border-white/10'
        }
      />
      {target && (
        <div
          ref={overlayRef}
          aria-hidden="true"
          className={`pointer-events-none absolute inset-0 rounded-2xl cap-event-overlay cap-event-${target.event_type}`}
        />
      )}
    </div>
  )
}
