import { ProgressBar } from '../ui/ProgressBar'

interface InterviewProgressProps {
  asked: number
  answered: number
}

export function InterviewProgress({ asked, answered }: InterviewProgressProps) {
  const label = `${answered} answered · ${asked} asked`
  return <ProgressBar value={answered} max={Math.max(1, asked)} label={label} />
}
