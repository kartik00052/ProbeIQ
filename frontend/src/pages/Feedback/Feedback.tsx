import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AppLayout } from '../../layouts/AppLayout'
import { Logo } from '../../components/common/Logo'
import { Button } from '../../components/ui/Button'
import { FeedbackSummary } from '../../components/feedback/FeedbackSummary'
import { ImprovementSuggestions } from '../../components/feedback/ImprovementSuggestions'
import { useInterview } from '../../hooks/useInterview'
import { ROUTES } from '../../constants/routes'
import { toFeedbackViewModel } from '../../services/feedbackService'

export default function Feedback() {
  const { status, feedback, reset } = useInterview()
  const navigate = useNavigate()

  useEffect(() => {
    if (status !== 'complete' && status !== 'idle') navigate(ROUTES.interview)
    if (status === 'idle') navigate(ROUTES.setup)
  }, [status, navigate])

  const view = toFeedbackViewModel(feedback)

  return (
    <AppLayout>
      <nav className="flex items-center justify-between py-2">
        <Logo />
        <button type="button" onClick={reset} className="text-sm text-text-dim underline-offset-4 hover:text-accent hover:underline">
          New interview
        </button>
      </nav>

      <div className="flex flex-1 flex-col justify-center gap-6 py-10">
        <div className="flex flex-col gap-3">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-accent">Interview complete</p>
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">Your post-interview report</h1>
        </div>

        {view.summary ? (
          <FeedbackSummary summary={view.summary} strengths={view.strengths} gaps={view.gaps} />
        ) : (
          <p className="text-text-dim">No report was returned for this session.</p>
        )}
        <ImprovementSuggestions suggestions={view.next} />

        <div className="mt-4 flex flex-wrap gap-3">
          <Link to={ROUTES.setup} onClick={reset}>
            <Button variant="ghost">Take another interview</Button>
          </Link>
        </div>
      </div>
    </AppLayout>
  )
}
