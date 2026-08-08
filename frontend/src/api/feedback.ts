import type { InterviewFeedback } from '../types/feedback'

export interface FeedbackSections {
  strengths: string[]
  gaps: string[]
  next: string[]
}

export function toFeedbackSections(feedback: InterviewFeedback | null | undefined): FeedbackSections {
  return {
    strengths: feedback?.strengths ?? [],
    gaps: feedback?.gaps ?? [],
    next: feedback?.next ?? [],
  }
}
