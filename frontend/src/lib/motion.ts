import type { Transition } from 'framer-motion'

export const springs = {
  snappy: { type: 'spring', stiffness: 400, damping: 30 } satisfies Transition,
  ui: { type: 'spring', stiffness: 200, damping: 25 } satisfies Transition,
} as const

export const depthTransition = {
  ...springs.ui,
  mass: 0.6,
} satisfies Transition
