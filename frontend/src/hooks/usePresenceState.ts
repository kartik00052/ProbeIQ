import { useEffect, useRef, useState } from 'react'
import { useInterviewStore } from '../stores/interviewStore'
import type { InterviewStatus } from '../types/interview'

export type PresenceState = 'idle' | 'thinking' | 'responding' | 'waiting' | 'complete'

export function usePresenceState(): PresenceState {
  const status = useInterviewStore((s) => s.status)
  const [responding, setResponding] = useState(false)
  const previousStatus = useRef<InterviewStatus>(status)

  useEffect(() => {
    if (previousStatus.current === 'thinking' && status === 'active') {
      setResponding(true)
      const timer = window.setTimeout(() => setResponding(false), 900)
      return () => window.clearTimeout(timer)
    }
    return undefined
  }, [status])

  useEffect(() => {
    previousStatus.current = status
  }, [status])

  if (responding) return 'responding'
  if (status === 'thinking') return 'thinking'
  if (status === 'complete') return 'complete'
  if (status === 'active') return 'waiting'
  return 'idle'
}
