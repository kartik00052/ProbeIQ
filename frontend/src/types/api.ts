import type { Candidate } from './candidate'
import type { InterviewFeedback } from './feedback'

export interface InterviewStartPayload {
  sessionId: string
  candidate: Candidate
}

export interface InterviewTurnPayload {
  sessionId: string
  message: string
}

export type InterviewPayload = InterviewStartPayload | InterviewTurnPayload

export interface InterviewResponse {
  reply: string
  done: boolean
  feedback?: InterviewFeedback | null
}

export interface ApiErrorBody {
  error: string
  detail: string
}
