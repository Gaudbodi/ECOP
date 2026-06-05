import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * cn() — class-name merge utility.
 *
 * Combines `clsx` (conditional class strings) with `tailwind-merge` (resolves
 * Tailwind utility conflicts so the last one wins, e.g. `px-2 px-4` -> `px-4`).
 *
 * RESEARCH.md "Don't Hand-Roll" — every component below uses this; do not
 * sprinkle bespoke joinClassNames helpers around the codebase.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
