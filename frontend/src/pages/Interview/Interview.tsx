import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { AppLayout } from '../../layouts/AppLayout'
import { InterviewHeader } from '../../components/interview/InterviewHeader'
import { InterviewTimer } from '../../components/interview/InterviewTimer'
import { InterviewProgress } from '../../components/interview/InterviewProgress'
import { QuestionCard } from '../../components/interview/QuestionCard'
import { AnswerInput } from '../../components/interview/AnswerInput'
import { AIThinkingIndicator } from '../../components/interview/AIThinkingIndicator'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { useInterview } from '../../hooks/useInterview'
import { ROUTES } from '../../constants/routes'
import { fadeUpVariants } from '../../components/animations/variants'

export default function Interview() {
  const { status, transcript, error, lastReply, answer } = useInterview()
  const navigate = useNavigate()
  const transcriptEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (status === 'complete') navigate(ROUTES.complete)
  }, [status, navigate])

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript.length])

  const asked = Math.ceil(transcript.length / 2)
  const answered = Math.floor(transcript.length / 2)
  const waitingForAnswer = status === 'active'
  const thinking = status === 'thinking'

  return (
    <AppLayout>
      <InterviewHeader>
        <div className="flex items-center gap-4">
          <InterviewTimer paused={status !== 'active'} />
          <InterviewProgress asked={asked} answered={answered} />
        </div>
      </InterviewHeader>

      <div className="flex flex-1 flex-col justify-end gap-6 py-8">
        <div className="flex max-h-[50vh] flex-col gap-3 overflow-y-auto pr-2">
          {transcript.slice(0, -1).map((message) => (
            <motion.div
              key={message.id}
              variants={fadeUpVariants}
              initial="initial"
              animate="animate"
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                message.role === 'candidate'
                  ? 'self-end bg-accent/10 text-text'
                  : 'self-start bg-surface text-text-dim'
              }`}
            >
              {message.text}
            </motion.div>
          ))}
          <div ref={transcriptEndRef} />
        </div>

        {waitingForAnswer && lastReply && (
          <QuestionCard text={lastReply} index={asked} />
        )}
        {thinking && <AIThinkingIndicator />}

        <AnimatePresence>
          {error && (
            <motion.div key={error} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <ErrorMessage message={error} />
            </motion.div>
          )}
        </AnimatePresence>

        <AnswerInput disabled={thinking} onSubmit={answer} />
      </div>
    </AppLayout>
  )
}
