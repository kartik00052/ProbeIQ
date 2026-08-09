import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { AppLayout } from '../../layouts/AppLayout'
import { Logo } from '../../components/common/Logo'
import { Button } from '../../components/ui/Button'
import { FeedbackSummary } from '../../components/feedback/FeedbackSummary'
import { ImprovementSuggestions } from '../../components/feedback/ImprovementSuggestions'
import { staggerContainer, revealItemVariants } from '../../components/animations/variants'
import { useInterview } from '../../hooks/useInterview'
import { ROUTES } from '../../constants/routes'
import { toFeedbackViewModel } from '../../services/feedbackService'
import { depthTransition } from '../../lib/motion'

export default function Feedback() {
  const { status, feedback, transcript, reset } = useInterview()
  const navigate = useNavigate()
  const reducedMotion = useReducedMotion()
  const [revealed, setRevealed] = useState(reducedMotion ?? false)
  const completeHeadingRef = useRef<HTMLHeadingElement>(null)
  const reportHeadingRef = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    if (status !== 'complete' && status !== 'idle') navigate(ROUTES.interview)
    if (status === 'idle') navigate(ROUTES.setup)
  }, [status, navigate])

  useEffect(() => {
    if (revealed) return
    const timer = window.setTimeout(() => setRevealed(true), 700)
    return () => window.clearTimeout(timer)
  }, [revealed])

  const confirmExit = (): boolean =>
    transcript.length === 0 ||
    window.confirm('Start over? Your current interview and report will be discarded.')

  const view = toFeedbackViewModel(feedback)

  return (
    <AppLayout>
      <nav className="flex items-center justify-between py-2">
        <Logo />
        <button
          type="button"
          onClick={() => {
            if (confirmExit()) reset()
          }}
          className="text-sm text-text-dim underline-offset-4 hover:text-accent hover:underline"
        >
          New interview
        </button>
      </nav>

      <div className="flex flex-1 flex-col justify-center gap-8 py-10">
        <AnimatePresence mode="wait">
          {!revealed ? (
            <motion.div
              key="complete"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={depthTransition}
              onAnimationComplete={() => completeHeadingRef.current?.focus()}
              className="flex flex-col gap-3"
            >
              <p className="font-mono text-xs uppercase tracking-[0.3em] text-accent">Interview complete</p>
              <h1 ref={completeHeadingRef} tabIndex={-1} className="text-3xl font-semibold tracking-tight outline-none md:text-4xl">
                You&apos;ve finished your technical interview.
              </h1>
              <p className="text-text-dim">Preparing your debrief…</p>
            </motion.div>
          ) : (
            <motion.div
              key="debrief"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={depthTransition}
              onAnimationComplete={() => reportHeadingRef.current?.focus()}
              className="flex flex-col"
            >
              <motion.div variants={staggerContainer} initial="initial" animate="animate" className="flex flex-col gap-6">
                <motion.div variants={revealItemVariants} className="flex flex-col gap-3">
                  <p className="font-mono text-xs uppercase tracking-[0.3em] text-accent">Debrief</p>
                  <h1 ref={reportHeadingRef} tabIndex={-1} className="text-3xl font-semibold tracking-tight outline-none md:text-4xl">Your post-interview report</h1>
                </motion.div>

                <motion.div variants={revealItemVariants}>
                  {view.summary ? (
                    <FeedbackSummary summary={view.summary} strengths={view.strengths} gaps={view.gaps} />
                  ) : (
                    <p className="text-text-dim">No report was returned for this session.</p>
                  )}
                </motion.div>
                <motion.div variants={revealItemVariants}>
                  <ImprovementSuggestions suggestions={view.next} />
                </motion.div>

                <motion.div variants={revealItemVariants} className="mt-4 flex flex-wrap gap-3">
                  <Link
                    to={ROUTES.setup}
                    onClick={(event) => {
                      if (!confirmExit()) event.preventDefault()
                      else reset()
                    }}
                  >
                    <Button variant="ghost">Take another interview</Button>
                  </Link>
                </motion.div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AppLayout>
  )
}
