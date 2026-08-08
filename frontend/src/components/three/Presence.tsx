import { Suspense, lazy } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import type { PresenceState } from '../../hooks/usePresenceState'

const PresenceScene = lazy(() => import('./PresenceScene'))

interface PresenceProps {
  state: PresenceState
}

export function Presence({ state }: PresenceProps) {
  const reducedMotion = useReducedMotion()

  if (reducedMotion) {
    return (
      <motion.div
        className="pointer-events-none absolute inset-0"
        animate={{ opacity: state === 'complete' ? 0.2 : 0.5 }}
        aria-hidden="true"
      >
        <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/15 blur-3xl" />
      </motion.div>
    )
  }

  return (
    <motion.div
      className="pointer-events-none absolute inset-0"
      initial={{ opacity: 0 }}
      animate={{ opacity: state === 'complete' ? 0.15 : 1 }}
      transition={{ duration: 1.2, ease: 'easeInOut' }}
      aria-hidden="true"
    >
      <Suspense fallback={null}>
        <PresenceScene state={state} />
      </Suspense>
    </motion.div>
  )
}
