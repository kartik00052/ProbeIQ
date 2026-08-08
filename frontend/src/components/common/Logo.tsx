export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2 font-semibold tracking-tight">
      <span className="h-2.5 w-2.5 rounded-full bg-accent" aria-hidden="true" />
      {!compact && <span className="text-lg text-text">Probe<span className="text-accent">IQ</span></span>}
    </span>
  )
}
