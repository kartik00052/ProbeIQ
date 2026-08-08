interface ErrorMessageProps {
  message: string
  onRetry?: () => void
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="rounded-xl border border-danger/40 bg-danger/10 p-4" role="alert">
      <p className="text-sm text-danger">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="mt-2 text-sm font-medium text-accent hover:underline">
          Try again
        </button>
      )}
    </div>
  )
}
