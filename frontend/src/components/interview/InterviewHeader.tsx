import type { ReactNode } from 'react'
import { Logo } from '../common/Logo'

interface InterviewHeaderProps {
  topic?: string | null
  children?: ReactNode
}

export function InterviewHeader({ topic, children }: InterviewHeaderProps) {
  return (
    <header className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <Logo />
        {topic && <span className="hidden font-mono text-xs text-text-dim sm:inline">{topic}</span>}
      </div>
      {children}
    </header>
  )
}
