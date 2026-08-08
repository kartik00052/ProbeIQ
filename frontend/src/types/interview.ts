export type InterviewStatus = 'idle' | 'active' | 'thinking' | 'complete'

export type TranscriptRole = 'interviewer' | 'candidate'

export interface TranscriptMessage {
  id: string
  role: TranscriptRole
  text: string
  timestamp: number
}
