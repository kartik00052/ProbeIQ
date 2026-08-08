export interface CandidateMember {
  id: string
  name: string
  jobRole: string
  yearsExperience: number
  education: string
  status: string
}

export interface Mission {
  day: number
  title: string
  passed: boolean | null
  skipped: boolean | null
  attempts: number | null
}

export interface CandidateSignals {
  commitDays: number
  missionsCompleted: number
  missionsFirstTry: number
}

export interface Candidate {
  member: CandidateMember
  missions: Mission[]
  signals: CandidateSignals
}
