import { AnimatePresence, motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { questionVariants } from '../animations/variants'

interface InterviewTransitionProps {
  transitionKey: string | number
  children: ReactNode
}

export function InterviewTransition({ transitionKey, children }: InterviewTransitionProps) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={transitionKey}
        variants={questionVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        className="flex flex-col gap-4"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
