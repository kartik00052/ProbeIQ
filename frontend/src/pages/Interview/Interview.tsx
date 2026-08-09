import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { AppLayout } from '../../layouts/AppLayout'
import { InterviewHeader } from '../../components/interview/InterviewHeader'
import { InterviewTimer } from '../../components/interview/InterviewTimer'
import { InterviewProgress } from '../../components/interview/InterviewProgress'
import { QuestionCard } from '../../components/interview/QuestionCard'
import { AnswerInput } from '../../components/interview/AnswerInput'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { useInterview } from '../../hooks/useInterview'
import { useInterviewStore } from '../../stores/interviewStore'
import { ROUTES } from '../../constants/routes'

export default function Interview() {
  const { status, transcript, error, lastReply, candidate, answer, retry } = useInterview()
  const navigate = useNavigate()
  const historyEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (status === 'complete') navigate(ROUTES.complete)
    else if (status === 'idle') navigate(ROUTES.setup)
  }, [status, navigate])

  useEffect(() => {
    const onPopState = () => {
      const s = useInterviewStore.getState().status
      if (s === 'complete') navigate(ROUTES.complete, { replace: true })
      else if (s === 'idle') navigate(ROUTES.setup, { replace: true })
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [navigate])

  useEffect(() => {
    const el = historyEndRef.current
    if (!el) return
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    if (distanceFromBottom < 96) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [transcript.length])

  const asked = Math.ceil(transcript.length / 2)
  const thinking = status === 'thinking'
  const history =
    transcript.length > 0 && transcript[transcript.length - 1].role === 'interviewer'
      ? transcript.slice(0, -1)
      : transcript

  return (
    <AppLayout>
      <InterviewHeader topic={candidate?.member.jobRole}>
        <InterviewTimer paused={status !== 'active'} />
      </InterviewHeader>

      {candidate && <InterviewProgress missions={candidate.missions} />}

      <div className="flex flex-1 flex-col justify-end gap-6 pt-8">
        {lastReply && (
          <div className="sticky top-0 z-10 -mx-6 bg-bg/85 px-6 pb-4 pt-2 backdrop-blur-md">
            <QuestionCard text={lastReply} index={asked} />
          </div>
        )}

        {history.length > 0 && (
          <div
            ref={historyEndRef}
            role="region"
            className="flex max-h-[34vh] flex-col gap-4 overflow-y-auto pr-2"
            aria-label="Interview transcript so far"
          >
            {history.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, ease: 'easeOut' }}
                className={`flex flex-col gap-1 ${
                  message.role === 'candidate' ? 'items-end self-end' : 'items-start self-start'
                }`}
              >
                <span className="font-mono text-xs uppercase tracking-widest text-text-dim/70">
                  {message.role === 'candidate' ? 'You' : 'Interviewer'}
                </span>
                <p
                  className={`break-words text-sm leading-relaxed ${
                    message.role === 'candidate' ? 'text-text' : 'text-text-dim'
                  }`}
                >
                  {message.text}
                </p>
              </motion.div>
            ))}
          </div>
        )}

        <div className="sticky bottom-0 z-10 -mx-6 flex flex-col gap-2 bg-bg/85 px-6 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-3 -mb-8 backdrop-blur-md">
          <AnimatePresence>
          {error && (
            <motion.div
              key={error}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <ErrorMessage message={error} onRetry={retry} />
            </motion.div>
          )}
        </AnimatePresence>

        <AnswerInput disabled={thinking} onSubmit={answer} />
        </div>
      </div>
    </AppLayout>
  )
}
