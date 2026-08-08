import { Link } from 'react-router-dom'
import { AppLayout } from '../../layouts/AppLayout'
import { Logo } from '../../components/common/Logo'
import { Button } from '../../components/ui/Button'
import { ROUTES } from '../../constants/routes'

export default function LandingPage() {
  return (
    <AppLayout>
      <nav className="flex justify-between py-2">
        <Logo />
        <Link to={ROUTES.setup} className="text-sm text-text-dim underline-offset-4 hover:text-accent hover:underline">
          Skip intro
        </Link>
      </nav>

      <div className="flex flex-1 flex-col items-center justify-center gap-8 text-center">
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-accent">AI technical interview agent</p>
        <h1 className="max-w-2xl text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
          Prove your skills with a <span className="text-accent">human-calibrated</span> AI interviewer.
        </h1>
        <p className="max-w-lg text-lg leading-relaxed text-text-dim">
          A 31-day AI-cohort curriculum becomes a live, adaptive interview. Your answers are probed in depth and
          turned into an honest post-interview report.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link to={ROUTES.setup}>
            <Button>Begin interview</Button>
          </Link>
        </div>
      </div>
    </AppLayout>
  )
}
