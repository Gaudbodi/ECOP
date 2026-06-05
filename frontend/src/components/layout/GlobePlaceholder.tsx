import { useEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import Globe from 'react-globe.gl'
import type { GlobeMethods } from 'react-globe.gl'
import { useTheme } from '../../hooks/useTheme'
import { ARCS, CITIES } from '../../data/cityAnchors'

/**
 * GlobePlaceholder — spinning react-globe.gl backdrop.
 *
 * Renders a low-saturation globe behind every tab, auto-rotates around
 * Ghana's longitude, and animates great-circle arcs anchored at Accra.
 * The component absorbs its container size; do NOT make it change document
 * flow. The `fixed inset-0 z-0 pointer-events-none` wrapper is the contract
 * App.tsx and the navbar/main panel rely on for stacking.
 */
export function GlobePlaceholder() {
  const { theme } = useTheme()
  const wrapRef = useRef<HTMLDivElement | null>(null)
  const globeRef = useRef<GlobeMethods | undefined>(undefined)
  const [size, setSize] = useState({ w: 0, h: 0 })
  const [ready, setReady] = useState(false)

  useEffect(() => {
    function measure() {
      if (!wrapRef.current) return
      setSize({
        w: wrapRef.current.clientWidth,
        h: wrapRef.current.clientHeight,
      })
    }
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [])

  useEffect(() => {
    const g = globeRef.current
    if (!g) return
    // Centre on Ghana, slow auto-rotate, no zoom (decorative).
    g.pointOfView({ lat: 7.95, lng: -1.02, altitude: 2.4 }, 0)
    const controls = g.controls() as unknown as {
      autoRotate: boolean
      autoRotateSpeed: number
      enableZoom: boolean
      enablePan: boolean
    }
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.5
    controls.enableZoom = false
    controls.enablePan = false
    setReady(true)
  }, [size])

  const dark = theme === 'dark'
  const globeImage = dark
    ? '//unpkg.com/three-globe/example/img/earth-night.jpg'
    : '//unpkg.com/three-globe/example/img/earth-day.jpg'
  const bumpImage = '//unpkg.com/three-globe/example/img/earth-topology.png'

  return (
    <div
      ref={wrapRef}
      aria-hidden="true"
      className="fixed inset-0 z-0 pointer-events-none overflow-hidden"
    >
      {/* Globe is the hero layer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: ready ? (dark ? 0.8 : 0.55) : 0 }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
        className="absolute inset-0"
      >
        {size.w > 0 && (
          <Globe
            ref={globeRef}
            width={size.w}
            height={size.h}
            backgroundColor="rgba(0,0,0,0)"
            globeImageUrl={globeImage}
            bumpImageUrl={bumpImage}
            atmosphereColor={dark ? '#38bdf8' : '#0284c7'}
            atmosphereAltitude={0.22}
            arcsData={ARCS}
            arcColor={(d: object) => (d as { color: [string, string] }).color}
            arcDashLength={0.45}
            arcDashGap={0.18}
            arcDashAnimateTime={3200}
            arcStroke={0.45}
            arcAltitudeAutoScale={0.45}
            pointsData={CITIES}
            pointLat={(d: object) => (d as { lat: number }).lat}
            pointLng={(d: object) => (d as { lng: number }).lng}
            pointAltitude={0}
            pointRadius={(d: object) =>
              (d as { size: number; ghana?: boolean }).ghana ? 0.55 : 0.32
            }
            pointColor={(d: object) =>
              (d as { ghana?: boolean }).ghana ? '#38bdf8' : '#a78bfa'
            }
            labelsData={CITIES.filter((c) => c.ghana)}
            labelLat={(d: object) => (d as { lat: number }).lat}
            labelLng={(d: object) => (d as { lng: number }).lng}
            labelText={(d: object) => (d as { name: string }).name}
            labelSize={0.45}
            labelDotRadius={0.2}
            labelColor={() => (dark ? 'rgba(248,250,252,0.85)' : 'rgba(15,23,42,0.85)')}
            labelResolution={2}
            animateIn
          />
        )}
      </motion.div>

      {/* Soft accent gradient to tie the globe into the glass surfaces. */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="absolute inset-0"
        style={{
          background: dark
            ? 'radial-gradient(ellipse at 80% 0%, rgba(56,189,248,0.18) 0%, rgba(2,6,23,0) 55%), radial-gradient(ellipse at 0% 100%, rgba(139,92,246,0.18) 0%, rgba(2,6,23,0) 55%)'
            : 'radial-gradient(ellipse at 80% 0%, rgba(56,189,248,0.10) 0%, rgba(241,245,249,0) 55%), radial-gradient(ellipse at 0% 100%, rgba(139,92,246,0.10) 0%, rgba(241,245,249,0) 55%)',
        }}
      />
    </div>
  )
}
