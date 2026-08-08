export type DepthLevel = 'none' | 'shallow' | 'moderate' | 'deep' | 'excellent'

export type AnswerQuality = 'strong' | 'adequate' | 'weak'

export interface DimensionScores {
  technical_correctness: number
  conceptual_depth: number
  reasoning_quality: number
  practical_understanding: number
  tradeoff_awareness: number
  communication_clarity: number
}

export interface Evaluation {
  score: number
  assessment: string
  strengths: string[]
  missing_concepts: string[]
  misconceptions: string[]
  depth_level: DepthLevel
  follow_up_needed: boolean
  follow_up_reason?: string | null
  recommended_probe?: string | null
}
