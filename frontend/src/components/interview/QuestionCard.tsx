import { motion } from 'framer-motion'
import { questionVariants } from '../animations/variants'

interface QuestionCardProps {
  text: string
  index: number
}

export function QuestionCard({ text, index }: QuestionCardProps) {
  return (
    <motion.article
      key={index}
      variants={questionVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      style={{ transformStyle: 'preserve-3d' }}
      className="relative"
    >
      <div className="mb-2 font-mono text-xs uppercase tracking-widest text-accent">Question {index}</div>
      <p className="text-xl leading-relaxed text-text md:text-2xl">{text}</p>
    </motion.article>
  )
}
