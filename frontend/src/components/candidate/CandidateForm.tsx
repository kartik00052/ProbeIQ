import { useState } from 'react'
import { SAMPLE_CANDIDATE } from '../../api/candidate'
import { parseCandidate } from '../../services/candidateService'
import type { Candidate } from '../../types/candidate'
import { Button } from '../ui/Button'

interface CandidateFormProps {
  onStart: (candidate: Candidate) => void
  loading: boolean
}

export function CandidateForm({ onStart, loading }: CandidateFormProps) {
  const [value, setValue] = useState(() => JSON.stringify(SAMPLE_CANDIDATE, null, 2))
  const [error, setError] = useState<string | null>(null)

  const submit = () => {
    try {
      onStart(parseCandidate(value))
    } catch (cause) {
      if (cause instanceof Error) setError(cause.message)
      else setError('Candidate data is invalid.')
    }
  }

  return (
    <div className="flex w-full flex-col gap-4">
      <div>
        <label htmlFor="candidate-json" className="mb-2 block font-mono text-xs uppercase tracking-widest text-text-dim">
          Candidate profile (JSON)
        </label>
        <textarea
          id="candidate-json"
          value={value}
          onChange={(event) => {
            setValue(event.target.value)
            setError(null)
          }}
          rows={14}
          spellCheck={false}
          aria-label="Candidate profile JSON"
          className="w-full resize-y rounded-2xl border border-line bg-surface/80 p-4 font-mono text-xs leading-relaxed text-text focus:border-accent focus:outline-none"
        />
        {error && <p className="mt-2 text-sm text-danger">{error}</p>}
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => {
            setValue(JSON.stringify(SAMPLE_CANDIDATE, null, 2))
            setError(null)
          }}
          className="text-sm text-text-dim underline-offset-4 hover:text-accent hover:underline"
        >
          Load sample profile
        </button>
        <Button onClick={submit} disabled={loading}>
          {loading ? 'Starting…' : 'Begin interview'}
        </Button>
      </div>
    </div>
  )
}
