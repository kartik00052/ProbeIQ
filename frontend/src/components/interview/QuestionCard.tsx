import { AnimatePresence, motion } from 'framer-motion'
import { questionVariants } from '../animations/variants'

interface QuestionCardProps {
  text: string
  index: number
}

export function QuestionCard({ text, index }: QuestionCardProps) {
  return (
    <div className="relative" style={{ perspective: '1200px' }}>
      <AnimatePresence mode="wait">
        <motion.article
          key={index}
          variants={questionVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          aria-live="polite"
          className="relative"
        >
          <header className="mb-3 flex items-baseline justify-between gap-4">
            <span className="font-mono text-xs uppercase tracking-widest text-accent">Interviewer</span>
            <span className="font-mono text-xs tabular-nums text-text-dim">
              Q{String(index).padStart(2, '0')}
            </span>
          </header>
          <p className="break-words text-2xl leading-snug tracking-tight text-text md:text-3xl md:leading-tight">{text}</p>
        </motion.article>
      </AnimatePresence>
    </div>
  )
}
