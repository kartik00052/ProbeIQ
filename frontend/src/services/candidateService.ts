import { z } from 'zod'
import type { Candidate } from '../types/candidate'

const missionSchema = z.object({
  day: z.number().int().positive(),
  title: z.string().min(1),
  passed: z.boolean().nullable(),
  skipped: z.boolean().nullable(),
  attempts: z.number().int().positive().nullable(),
})

export const candidateSchema = z.object({
  member: z.object({
    id: z.string().min(1),
    name: z.string().min(1),
    jobRole: z.string().min(1),
    yearsExperience: z.number().int().nonnegative(),
    education: z.string().min(1),
    status: z.string().min(1),
  }),
  missions: z.array(missionSchema),
  signals: z.object({
    commitDays: z.number().int().nonnegative(),
    missionsCompleted: z.number().int().nonnegative(),
    missionsFirstTry: z.number().int().nonnegative(),
  }),
})

export function parseCandidate(value: string): Candidate {
  const parsed = candidateSchema.parse(JSON.parse(value))
  return parsed
}
