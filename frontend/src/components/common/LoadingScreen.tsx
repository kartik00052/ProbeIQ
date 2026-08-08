import { motion } from 'framer-motion'
import { Logo } from './Logo'

export function LoadingScreen({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6" role="status" aria-live="polite">
      <motion.div
        animate={{ opacity: [1, 0.5, 1], scale: [1, 1.04, 1] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
      >
        <Logo />
      </motion.div>
      <p className="font-mono text-xs uppercase tracking-widest text-text-dim">{label}</p>
    </div>
  )
}
