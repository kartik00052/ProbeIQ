import { Card } from '../ui/Card'

interface FeedbackSummaryProps {
  summary: string
  strengths: string[]
  gaps: string[]
}

export function FeedbackSummary({ summary, strengths, gaps }: FeedbackSummaryProps) {
  return (
    <div className="flex flex-col gap-6">
      <Card elevated className="p-6">
        <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-accent">Summary</h2>
        <p className="break-words leading-relaxed text-text">{summary}</p>
      </Card>

      {strengths.length > 0 && (
        <Card className="p-6">
          <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-accent">What you demonstrated</h3>
          <ul className="flex list-none flex-col gap-2">
            {strengths.map((item) => (
              <li key={item} className="flex gap-2 text-text">
                <span className="text-accent">+</span>
                <span className="break-words">{item}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {gaps.length > 0 && (
        <Card className="p-6">
          <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-text-dim">Where to go deeper</h3>
          <ul className="flex list-none flex-col gap-2">
            {gaps.map((item) => (
              <li key={item} className="flex gap-2 text-text">
                <span className="text-text-dim">–</span>
                <span className="break-words">{item}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
