import { useCallback } from 'react'
import { useInterviewStore } from '../stores/interviewStore'
import type { Candidate } from '../types/candidate'

export function useInterview() {
  const status = useInterviewStore((s) => s.status)
  const sessionId = useInterviewStore((s) => s.sessionId)
  const candidate = useInterviewStore((s) => s.candidate)
  const transcript = useInterviewStore((s) => s.transcript)
  const feedback = useInterviewStore((s) => s.feedback)
  const error = useInterviewStore((s) => s.error)
  const lastReply = useInterviewStore((s) => s.lastReply)

  const start = useCallback((candidate: Candidate) => useInterviewStore.getState().start(candidate), [])
  const answer = useCallback((message: string) => useInterviewStore.getState().answer(message), [])
  const reset = useCallback(() => useInterviewStore.getState().reset(), [])

  return { status, sessionId, candidate, transcript, feedback, error, lastReply, start, answer, reset }
}
