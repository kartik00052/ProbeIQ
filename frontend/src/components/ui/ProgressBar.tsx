import { motion } from 'framer-motion'

interface ProgressBarProps {
  value: number
  max: number
  label?: string
}

export function ProgressBar({ value, max, label }: ProgressBarProps) {
  const safeMax = Math.max(1, max)
  const percent = Math.min(100, Math.round((value / safeMax) * 100))
  return (
    <div
      className="flex w-full items-center gap-3"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
      aria-label={label}
    >
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-line/40">
        <motion.div
          className="h-full rounded-full bg-accent"
          initial={false}
          animate={{ width: `${percent}%` }}
          transition={{ type: 'spring', stiffness: 120, damping: 24 }}
        />
      </div>
      {label && <span className="text-xs font-mono text-text-dim">{label}</span>}
    </div>
  )
}
