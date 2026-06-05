import type { ComponentPropsWithoutRef } from 'react'
import { cn } from '../../lib/cn'

type GlassVariant = 'card' | 'navbar' | 'item'

export interface GlassCardProps extends ComponentPropsWithoutRef<'div'> {
  variant?: GlassVariant
}

// Maps the variant prop to the corresponding @utility rule defined in
// frontend/src/index.css. PATTERNS.md "Glassmorphic styling" notes the
// Jinja codebase only has three flavors — keep the API tight; do NOT
// reach for class-variance-authority for a 3-key map.
const variantClass: Record<GlassVariant, string> = {
  card: 'glass-card',
  navbar: 'glass-navbar',
  item: 'glass-item',
}

/**
 * GlassCard — wraps the three glass utilities from index.css.
 *
 * - `variant="card"`   -> `.glass-card`   (default; for surface panels)
 * - `variant="navbar"` -> `.glass-navbar` (for the top nav bar)
 * - `variant="item"`   -> `.glass-item`   (for clickable list items, e.g. AlertCard in Plan 03)
 *
 * Pass any extra Tailwind utilities via `className` — `cn()` deduplicates
 * conflicts (e.g. `<GlassCard className="rounded-none" />` overrides the
 * default rounded radius from the @utility rule when needed for the navbar).
 */
export function GlassCard({ variant = 'card', className, ...rest }: GlassCardProps) {
  return <div className={cn(variantClass[variant], className)} {...rest} />
}
