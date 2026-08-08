import type { Transition } from 'framer-motion'

export const springs = {
  snappy: { type: 'spring', stiffness: 400, damping: 30 } satisfies Transition,
  ui: { type: 'spring', stiffness: 200, damping: 25 } satisfies Transition,
  gentle: { type: 'spring', stiffness: 100, damping: 20 } satisfies Transition,
} as const

export const depthTransition = {
  ...springs.ui,
  mass: 0.6,
} satisfies Transition

export const PRESENTATION = {
  perspective: '1200px',
  questionStartZ: -100,
  presenceBreath: { y: [0, -6, 0], scale: [1, 1.02, 1] },
} as const
