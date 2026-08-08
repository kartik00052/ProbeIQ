import { Card } from '../ui/Card'

interface ImprovementSuggestionsProps {
  suggestions: string[]
}

export function ImprovementSuggestions({ suggestions }: ImprovementSuggestionsProps) {
  if (suggestions.length === 0) return null
  return (
    <Card className="p-6">
      <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-accent">Next steps</h3>
      <ol className="flex list-none flex-col gap-3">
        {suggestions.map((item) => (
          <li key={item} className="flex gap-3 text-text">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/15 font-mono text-xs text-accent">
              {suggestions.indexOf(item) + 1}
            </span>
            <span>{item}</span>
          </li>
        ))}
      </ol>
    </Card>
  )
}
