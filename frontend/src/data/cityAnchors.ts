/** Named city anchors for the spinning globe + great-circle arcs.
 *
 * Ghana hubs anchor the alert mesh; West-African neighbours give the arcs
 * something to span — the visual reads as a regional emergency comms graph.
 */

export interface City {
  name: string
  lat: number
  lng: number
  size: number
  ghana?: boolean
}

export const CITIES: City[] = [
  { name: 'Accra', lat: 5.6037, lng: -0.187, size: 1.4, ghana: true },
  { name: 'Kumasi', lat: 6.6885, lng: -1.6244, size: 1.1, ghana: true },
  { name: 'Tamale', lat: 9.4008, lng: -0.8393, size: 0.9, ghana: true },
  { name: 'Sekondi-Takoradi', lat: 4.9344, lng: -1.7133, size: 0.85, ghana: true },
  { name: 'Cape Coast', lat: 5.1054, lng: -1.2466, size: 0.7, ghana: true },
  { name: 'Sunyani', lat: 7.3349, lng: -2.3265, size: 0.7, ghana: true },
  { name: 'Bolgatanga', lat: 10.7856, lng: -0.8513, size: 0.7, ghana: true },
  { name: 'Ho', lat: 6.6, lng: 0.4713, size: 0.65, ghana: true },
  { name: 'Wa', lat: 10.0606, lng: -2.5057, size: 0.65, ghana: true },
  // Neighbours
  { name: 'Lomé', lat: 6.1319, lng: 1.2228, size: 0.6 },
  { name: 'Abidjan', lat: 5.3599, lng: -4.0083, size: 0.7 },
  { name: 'Ouagadougou', lat: 12.3714, lng: -1.5197, size: 0.6 },
  { name: 'Lagos', lat: 6.5244, lng: 3.3792, size: 0.8 },
  { name: 'Niamey', lat: 13.5117, lng: 2.1251, size: 0.55 },
]

/** Great-circle arcs anchored at Accra, plus a few cross-region. */
export interface Arc {
  startLat: number
  startLng: number
  endLat: number
  endLng: number
  color: [string, string]
}

const accent = '#0ea5e9'
const accent2 = '#8b5cf6'
const warn = '#f59e0b'

export const ARCS: Arc[] = [
  // Accra hub → all Ghana cities
  ...CITIES.filter((c) => c.ghana && c.name !== 'Accra').map((c) => ({
    startLat: 5.6037,
    startLng: -0.187,
    endLat: c.lat,
    endLng: c.lng,
    color: [accent, accent2] as [string, string],
  })),
  // Ghana → neighbours (Accra hub)
  ...CITIES.filter((c) => !c.ghana).map((c) => ({
    startLat: 5.6037,
    startLng: -0.187,
    endLat: c.lat,
    endLng: c.lng,
    color: [accent2, warn] as [string, string],
  })),
  // Cross-Ghana arcs to enrich the mesh
  { startLat: 6.6885, startLng: -1.6244, endLat: 9.4008, endLng: -0.8393, color: [accent, accent2] }, // Kumasi → Tamale
  { startLat: 4.9344, startLng: -1.7133, endLat: 6.6885, endLng: -1.6244, color: [accent2, accent] }, // Sekondi → Kumasi
  { startLat: 9.4008, startLng: -0.8393, endLat: 10.7856, endLng: -0.8513, color: [accent, accent2] }, // Tamale → Bolga
]
