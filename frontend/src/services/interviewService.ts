import { startInterview, sendMessage } from '../api/interview'
import type { Candidate } from '../types/candidate'
import type { InterviewResponse } from '../types/api'

export async function beginInterview(sessionId: string, candidate: Candidate): Promise<InterviewResponse> {
  return startInterview(sessionId, candidate)
}

export async function submitAnswer(sessionId: string, message: string): Promise<InterviewResponse> {
  return sendMessage(sessionId, message)
}
