import { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { INTERVIEW } from '../../constants/interview'
import { Button } from '../ui/Button'

interface AnswerInputProps {
  disabled: boolean
  onSubmit: (message: string) => void
}

export function AnswerInput({ disabled, onSubmit }: AnswerInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const canSubmit = !disabled && value.trim().length > 0

  const submit = () => {
    if (!canSubmit) return
    onSubmit(value.trim())
    setValue('')
  }

  return (
    <motion.div layout className="flex flex-col gap-3">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault()
            submit()
          }
        }}
        placeholder="Type your answer… (Enter to send, Shift+Enter for a new line)"
        maxLength={INTERVIEW.answerMaxLength}
        disabled={disabled}
        aria-label="Your answer"
        rows={4}
        className="w-full resize-none rounded-2xl border border-line bg-surface/80 p-4 text-text placeholder:text-text-dim/60 focus:border-accent focus:outline-none disabled:opacity-50"
      />
      <div className="flex items-center justify-between gap-4">
        <span className="font-mono text-xs text-text-dim">
          {value.length}/{INTERVIEW.answerMaxLength}
        </span>
        <Button onClick={submit} disabled={!canSubmit}>
          {disabled ? 'Thinking…' : 'Send answer'}
        </Button>
      </div>
    </motion.div>
  )
}
