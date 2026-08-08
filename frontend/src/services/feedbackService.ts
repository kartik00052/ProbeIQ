import type { InterviewFeedback } from '../types/feedback'

export interface FeedbackViewModel {
  summary: string
  strengths: string[]
  gaps: string[]
  next: string[]
}

export function toFeedbackViewModel(feedback: InterviewFeedback | null | undefined): FeedbackViewModel {
  return {
    summary: feedback?.summary ?? '',
    strengths: feedback?.strengths ?? [],
    gaps: feedback?.gaps ?? [],
    next: feedback?.next ?? [],
  }
}
