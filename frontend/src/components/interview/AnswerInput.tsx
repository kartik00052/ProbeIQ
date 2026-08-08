import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { INTERVIEW } from '../../constants/interview'
import { Button } from '../ui/Button'

interface AnswerInputProps {
  disabled: boolean
  onSubmit: (message: string) => Promise<boolean>
}

const swapTransition = { duration: 0.15 } as const

export function AnswerInput({ disabled, onSubmit }: AnswerInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const wasDisabled = useRef(disabled)
  const reducedMotion = useReducedMotion()

  const captured = disabled && value.trim().length > 0
  const canSubmit = !disabled && value.trim().length > 0

  const submit = async () => {
    if (!canSubmit) return
    const sent = await onSubmit(value.trim())
    if (sent) setValue('')
  }

  useEffect(() => {
    if (wasDisabled.current && !disabled) {
      const active = document.activeElement
      if (active === document.body || active === textareaRef.current) textareaRef.current?.focus()
    }
    wasDisabled.current = disabled
  }, [disabled])

  return (
    <section aria-labelledby="response-label" className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-4">
        <AnimatePresence mode="wait" initial={false}>
          {disabled ? (
            <motion.span
              key="thinking"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={swapTransition}
              role="status"
              className="font-mono text-xs uppercase tracking-widest text-accent"
            >
              <motion.span
                animate={reducedMotion ? { opacity: 1 } : { opacity: [0.45, 1, 0.45] }}
                transition={reducedMotion ? { duration: 0 } : { duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                className="inline-block"
              >
                The interviewer is analyzing your answer
              </motion.span>
            </motion.span>
          ) : (
            <motion.span
              key="label"
              id="response-label"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={swapTransition}
              className="font-mono text-xs uppercase tracking-widest text-text-dim"
            >
              Your response
            </motion.span>
          )}
        </AnimatePresence>
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={captured ? 'captured' : 'count'}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={swapTransition}
            className="font-mono text-xs tabular-nums text-text-dim/70"
          >
            {captured ? 'Response recorded' : `${value.length}/${INTERVIEW.answerMaxLength}`}
          </motion.span>
        </AnimatePresence>
      </div>

      <AnimatePresence mode="wait" initial={false}>
        {captured ? (
          <motion.div
            key="captured"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={swapTransition}
            className="flex items-center gap-3 rounded-xl border border-line bg-surface/60 px-4 py-3"
          >
            <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-accent" />
            <span className="font-mono text-xs text-text-dim">Waiting for the interviewer…</span>
          </motion.div>
        ) : (
          <motion.textarea
            key="input"
            ref={textareaRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={swapTransition}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                void submit()
              }
            }}
            placeholder="Explain your approach…"
            maxLength={INTERVIEW.answerMaxLength}
            disabled={disabled}
            aria-label="Your answer"
            rows={5}
            className="w-full resize-none rounded-xl border border-line bg-surface/60 p-4 text-base leading-relaxed text-text placeholder:text-text-dim/60 focus:border-accent focus:ring-2 focus:ring-accent/25 focus:outline-none disabled:cursor-not-allowed disabled:opacity-40 min-h-[10rem] md:min-h-[13rem]"
          />
        )}
      </AnimatePresence>

      <div className="flex items-center justify-between gap-4">
        <span className="hidden font-mono text-xs text-text-dim/70 sm:inline">
          Enter to send · Shift+Enter for a new line
        </span>
        <Button onClick={() => void submit()} disabled={!canSubmit}>
          {disabled ? 'Thinking…' : 'Submit'}
        </Button>
      </div>
    </section>
  )
}
