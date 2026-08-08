import { motion } from 'framer-motion'

export function AIThinkingIndicator() {
  return (
    <motion.div
      className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-accent"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      role="status"
      aria-label="Interviewer is thinking"
    >
      <motion.span
        className="h-1.5 w-1.5 rounded-full bg-accent"
        animate={{ opacity: [0.2, 1, 0.2], scale: [1, 1.4, 1] }}
        transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
      />
      Thinking
    </motion.div>
  )
}
