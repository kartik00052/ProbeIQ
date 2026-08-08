import { Suspense, lazy, useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import type { PresenceState } from '../../hooks/usePresenceState'
import { depthTransition } from '../../lib/motion'
import { PresenceErrorBoundary } from './PresenceErrorBoundary'

const PresenceScene = lazy(() => import('./PresenceScene'))

interface PresenceProps {
  state: PresenceState
  interviewing: boolean
}

const REST_OPACITY: Record<PresenceState, number> = {
  idle: 0.5,
  thinking: 0.42,
  responding: 0.46,
  waiting: 0.3,
  complete: 0.3,
}

function useLowPowerPoster(): boolean {
  return useMemo(() => {
    if (typeof navigator === 'undefined') return false
    const coarse = typeof window.matchMedia === 'function' && window.matchMedia('(pointer: coarse)').matches
    if (!coarse) return false
    const cpus = navigator.hardwareConcurrency ?? 8
    const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory ?? 8
    return cpus <= 4 && memory <= 4
  }, [])
}

function useWebGLSupported(): boolean {
  return useMemo(() => {
    if (typeof document === 'undefined') return false
    try {
      const canvas = document.createElement('canvas')
      return !!(canvas.getContext('webgl2') || canvas.getContext('webgl'))
    } catch {
      return false
    }
  }, [])
}

function PresencePoster() {
  return (
    <div className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/15 blur-3xl" />
  )
}

export function Presence({ state, interviewing }: PresenceProps) {
  const reducedMotion = useReducedMotion()
  const lowPower = useLowPowerPoster()
  const webglSupported = useWebGLSupported()
  const restOpacity = REST_OPACITY[state]

  if (reducedMotion || lowPower || !webglSupported) {
    return (
      <motion.div
        className="pointer-events-none absolute inset-0"
        initial={false}
        animate={{ opacity: interviewing ? restOpacity * 0.8 : restOpacity }}
        transition={{ duration: 0.3 }}
        aria-hidden="true"
      >
        <PresencePoster />
      </motion.div>
    )
  }

  return (
    <motion.div
      className="pointer-events-none absolute inset-0"
      initial={{ opacity: 1, scale: 1, y: 0 }}
      animate={{
        opacity: interviewing ? 0.52 : 1,
        scale: interviewing ? 0.8 : 1,
        y: interviewing ? 16 : 0,
      }}
      transition={depthTransition}
      aria-hidden="true"
    >
      <Suspense fallback={<PresencePoster />}>
        <PresenceErrorBoundary fallback={<PresencePoster />}>
          <PresenceScene state={state} interviewing={interviewing} />
        </PresenceErrorBoundary>
      </Suspense>
    </motion.div>
  )
}
