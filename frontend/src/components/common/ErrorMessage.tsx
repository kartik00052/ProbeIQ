interface ErrorMessageProps {
  message: string
  onRetry?: () => void
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div
      className="rounded-xl border border-danger/25 bg-surface/70 p-4"
      role="alert"
    >
      <p className="text-sm text-text">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 rounded-md text-sm font-medium text-accent outline-none hover:text-accent-bright focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          Try again
        </button>
      )}
    </div>
  )
}
