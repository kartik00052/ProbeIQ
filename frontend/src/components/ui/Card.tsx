import type { ComponentPropsWithoutRef } from 'react'

interface CardProps extends ComponentPropsWithoutRef<'div'> {
  elevated?: boolean
}

export function Card({ elevated = false, className, ...props }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-line/60 bg-surface/60 backdrop-blur-md ${
        elevated ? 'shadow-glow' : ''
      } ${className ?? ''}`}
      {...props}
    />
  )
}
