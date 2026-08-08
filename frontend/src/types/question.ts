export type QuestionType =
  | 'conceptual'
  | 'implementation'
  | 'architecture'
  | 'debugging'
  | 'scenario'
  | 'trade-off'
  | 'production'
  | 'follow-up'

export type Difficulty = 'foundational' | 'intermediate' | 'advanced'

export interface Question {
  question: string
  question_type: QuestionType
  curriculum_day: number
  topic: string
  difficulty: Difficulty
  purpose: string
}
