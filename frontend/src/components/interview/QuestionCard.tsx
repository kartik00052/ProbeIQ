import { AnimatePresence, motion } from 'framer-motion'
import { useMediaQuery } from '../../hooks/useMediaQuery'
import { questionVariants, questionVariantsMobile } from '../animations/variants'

interface QuestionCardProps {
  text: string
  index: number
}

export function QuestionCard({ text, index }: QuestionCardProps) {
  const isNarrow = useMediaQuery('(max-width: 640px)')
  const variants = isNarrow ? questionVariantsMobile : questionVariants
  return (
    <div className="relative" style={{ perspective: isNarrow ? '800px' : '1200px' }}>
      <AnimatePresence mode="wait">
        <motion.article
          key={index}
          variants={variants}
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
