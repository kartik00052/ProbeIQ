import type { Mission } from '../../types/candidate'

interface InterviewProgressProps {
  missions: Mission[]
  currentModuleId?: number | null
  coveredModuleIds?: number[]
}

type ModuleState = 'covered' | 'skipped' | 'open'

function moduleState(mission: Mission, coveredModuleIds: number[] | undefined): ModuleState {
  if (mission.passed === true) return 'covered'
  if (mission.skipped === true) return 'skipped'
  if (coveredModuleIds?.includes(mission.day)) return 'covered'
  return 'open'
}

const GLYPH: Record<ModuleState, string> = {
  covered: '●',
  skipped: '◇',
  open: '○',
}

const STATE_LABEL: Record<ModuleState, string> = {
  covered: 'Covered',
  skipped: 'Skipped',
  open: 'Not covered',
}

export function InterviewProgress({ missions, currentModuleId, coveredModuleIds }: InterviewProgressProps) {
  if (missions.length === 0) return null

  return (
    <section aria-label="Curriculum coverage" className="-mx-6 mt-8 flex items-center gap-4 overflow-x-auto px-6 pb-1">
      <span className="shrink-0 font-mono text-xs uppercase tracking-widest text-text-dim">Curriculum</span>
      <ul className="flex flex-wrap items-center gap-3">
        {missions.map((mission) => {
          const state = moduleState(mission, coveredModuleIds)
          const isCurrent = currentModuleId != null && currentModuleId === mission.day
          return (
            <li
              key={mission.day}
              title={mission.title}
              className={`flex items-center gap-1.5 font-mono text-xs tabular-nums ${
                isCurrent ? 'text-accent' : 'text-text-dim'
              }`}
            >
              <span
                aria-hidden="true"
                className={
                  isCurrent
                    ? 'text-accent'
                    : state === 'covered'
                      ? 'text-accent'
                      : state === 'skipped'
                        ? 'text-text-dim/40'
                        : 'text-text-dim/60'
                }
              >
                {isCurrent ? '◉' : GLYPH[state]}
              </span>
              <span>{String(mission.day).padStart(2, '0')}</span>
              <span className="sr-only">
                Day {mission.day}: {mission.title}. {isCurrent ? 'Current module' : STATE_LABEL[state]}.
              </span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
