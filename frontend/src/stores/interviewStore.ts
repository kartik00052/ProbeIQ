import { create } from 'zustand'
import type { Candidate } from '../types/candidate'
import type { InterviewFeedback } from '../types/feedback'
import type { InterviewStatus, TranscriptMessage } from '../types/interview'
import { beginInterview, submitAnswer } from '../services/interviewService'
import { toErrorMessage } from '../utils/errorHandler'

function createMessage(role: TranscriptMessage['role'], text: string): TranscriptMessage {
  return { id: crypto.randomUUID(), role, text, timestamp: Date.now() }
}

function newSessionId(): string {
  return crypto.randomUUID()
}

interface InterviewStore {
  status: InterviewStatus
  sessionId: string | null
  candidate: Candidate | null
  transcript: TranscriptMessage[]
  feedback: InterviewFeedback | null
  error: string | null
  lastReply: string | null
  failedAnswer: string | null
  engine: 'llm' | 'offline'
  engineModel: string | null
  start: (candidate: Candidate) => Promise<void>
  answer: (message: string) => Promise<boolean>
  retry: () => Promise<boolean>
  reset: () => void
}

export const useInterviewStore = create<InterviewStore>((set, get) => ({
  status: 'idle',
  sessionId: null,
  candidate: null,
  transcript: [],
  feedback: null,
  error: null,
  lastReply: null,
  failedAnswer: null,
  engine: 'offline',
  engineModel: null,

  start: async (candidate) => {
    if (get().status === 'thinking') return
    const sessionId = newSessionId()
    set({ status: 'thinking', sessionId, candidate, transcript: [], feedback: null, error: null, lastReply: null, failedAnswer: null, engine: 'offline', engineModel: null })
    try {
      const response = await beginInterview(sessionId, candidate)
      set((state) => ({
        status: response.done ? 'complete' : 'active',
        lastReply: response.reply,
        feedback: response.feedback ?? null,
        engine: response.engine ?? 'offline',
        engineModel: response.model ?? null,
        transcript: [...state.transcript, createMessage('interviewer', response.reply)],
      }))
    } catch (error) {
      set({ status: 'idle', error: toErrorMessage(error) })
    }
  },

  answer: async (message) => {
    const { sessionId, status } = get()
    if (!sessionId || status === 'thinking' || status === 'complete') return false
    const trimmed = message.trim()
    if (!trimmed) return false
    set((state) => ({
      status: 'thinking',
      error: null,
      transcript: [...state.transcript, createMessage('candidate', trimmed)],
    }))
    try {
      const response = await submitAnswer(sessionId, trimmed)
      set((state) => ({
        status: response.done ? 'complete' : 'active',
        lastReply: response.reply,
        feedback: response.feedback ?? null,
        engine: response.engine ?? 'offline',
        engineModel: response.model ?? null,
        failedAnswer: null,
        transcript: [...state.transcript, createMessage('interviewer', response.reply)],
      }))
      return true
    } catch (error) {
      set((state) => ({
        status: 'active',
        error: toErrorMessage(error),
        failedAnswer: trimmed,
        transcript: state.transcript.slice(0, -1),
      }))
      return false
    }
  },

  retry: async () => {
    const { failedAnswer } = get()
    if (!failedAnswer) return false
    return get().answer(failedAnswer)
  },

  reset: () =>
    set({
      status: 'idle',
      sessionId: null,
      candidate: null,
      transcript: [],
      feedback: null,
      error: null,
      lastReply: null,
      failedAnswer: null,
      engine: 'offline',
      engineModel: null,
    }),
}))
