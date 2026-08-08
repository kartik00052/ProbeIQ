import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppLayout } from '../../layouts/AppLayout'
import { CandidateForm } from '../../components/candidate/CandidateForm'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { Logo } from '../../components/common/Logo'
import { useInterview } from '../../hooks/useInterview'
import { ROUTES } from '../../constants/routes'

export default function CandidateSetup() {
  const { start, status, error, reset } = useInterview()
  const navigate = useNavigate()

  useEffect(() => {
    if (status === 'active') navigate(ROUTES.interview)
    if (status === 'complete') navigate(ROUTES.complete)
  }, [status, navigate])

  const loading = status === 'thinking'

  return (
    <AppLayout showPresence={false}>
      <nav className="flex justify-between py-2">
        <Logo />
        <button type="button" onClick={reset} className="text-sm text-text-dim underline-offset-4 hover:text-accent hover:underline">
          Reset
        </button>
      </nav>

      <div className="flex flex-1 flex-col justify-center py-10">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight md:text-4xl">Before we begin</h1>
        <p className="mb-8 max-w-lg leading-relaxed text-text-dim">
          Your curriculum profile shapes the interview. The profile is a single JSON payload the interviewer uses to
          plan questions.
        </p>
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} onRetry={reset} />
          </div>
        )}
        <CandidateForm onStart={start} loading={loading} />
      </div>
    </AppLayout>
  )
}
