import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { LoadingScreen } from '../common/LoadingScreen'
import { useAuth } from '../../hooks/useAuth'
import { ROUTES } from '../../constants/routes'

interface RequireAuthProps {
  children: ReactNode
}

/**
 * Route guard for authenticated-only pages. While the session cookie is being
 * probed on boot a loading screen is shown; guests are redirected to /login
 * (remembering where they were headed) and re-admitted after signing in.
 *
 * This is a UX guard only — the API enforces authentication server-side.
 */
export function RequireAuth({ children }: RequireAuthProps) {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <LoadingScreen label="Checking session" />
  if (status === 'unauthenticated') {
    return <Navigate to={ROUTES.login} replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}
