import { apiClient } from './client'
import type { Candidate } from '../types/candidate'
import type { InterviewResponse } from '../types/api'

export async function startInterview(sessionId: string, candidate: Candidate): Promise<InterviewResponse> {
  const { data } = await apiClient.post<InterviewResponse>('/interview', { sessionId, candidate })
  return data
}

export async function sendMessage(sessionId: string, message: string): Promise<InterviewResponse> {
  const { data } = await apiClient.post<InterviewResponse>('/interview', { sessionId, message })
  return data
}
