import { useEffect, useState } from 'react'

export function useInterviewTimer(paused: boolean) {
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    if (paused) return
    const startedAt = Date.now() - seconds * 1000
    const interval = window.setInterval(() => {
      setSeconds(Math.floor((Date.now() - startedAt) / 1000))
    }, 1000)
    return () => window.clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paused])

  return seconds
}
