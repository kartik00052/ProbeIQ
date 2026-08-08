import { useEffect, useRef, useState } from 'react'
import { useInterviewStore } from '../stores/interviewStore'
import type { InterviewStatus } from '../types/interview'

export type PresenceState = 'idle' | 'thinking' | 'responding' | 'waiting' | 'complete'

export interface PresenceView {
  state: PresenceState
  interviewing: boolean
}

export function usePresenceState(): PresenceView {
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

  const interviewing = status !== 'idle'

  if (responding) return { state: 'responding', interviewing }
  if (status === 'thinking') return { state: 'thinking', interviewing }
  if (status === 'complete') return { state: 'complete', interviewing }
  if (status === 'active') return { state: 'waiting', interviewing }
  return { state: 'idle', interviewing }
}
