import type { HTMLMotionProps } from 'framer-motion'
import { motion } from 'framer-motion'
import { springs } from '../../lib/motion'

type ButtonVariant = 'primary' | 'ghost'

interface ButtonProps extends HTMLMotionProps<'button'> {
  variant?: ButtonVariant
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-accent-ink hover:bg-accent-bright focus-visible:outline-accent rounded-full px-6 py-3 font-semibold transition-colors',
  ghost:
    'border border-line hover:border-accent/60 hover:text-accent rounded-full px-6 py-3 font-medium transition-colors',
}

export function Button({ variant = 'primary', className, children, disabled, ...props }: ButtonProps) {
  return (
    <motion.button
      whileHover={disabled ? undefined : { scale: 1.03 }}
      whileTap={disabled ? undefined : { scale: 0.97 }}
      transition={springs.snappy}
      className={`${variantClasses[variant]} disabled:pointer-events-none disabled:opacity-40 ${className ?? ''}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </motion.button>
  )
}
