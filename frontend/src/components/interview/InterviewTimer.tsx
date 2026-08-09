import { useInterviewTimer } from '../../hooks/useInterviewTimer'
import { formatTime } from '../../utils/formatTime'

interface InterviewTimerProps {
  paused: boolean
}

export function InterviewTimer({ paused }: InterviewTimerProps) {
  const seconds = useInterviewTimer(paused)
  return (
    <span aria-label="Elapsed time" className="font-mono text-sm text-text-dim">
      {formatTime(seconds)}
    </span>
  )
}
