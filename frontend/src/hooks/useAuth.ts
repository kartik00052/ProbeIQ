import { useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import type { User } from '../types/auth'

export function useAuth() {
  const status = useAuthStore((s) => s.status)
  const user = useAuthStore((s) => s.user)
  const error = useAuthStore((s) => s.error)

  const login = useCallback(
    (email: string, password: string): Promise<void> => useAuthStore.getState().login(email, password),
    [],
  )
  const register = useCallback(
    (email: string, password: string): Promise<void> => useAuthStore.getState().register(email, password),
    [],
  )
  const logout = useCallback((): Promise<void> => useAuthStore.getState().logout(), [])
  const refreshSession = useCallback((): Promise<void> => useAuthStore.getState().refreshSession(), [])

  return {
    status,
    user,
    error,
    isAuthenticated: status === 'authenticated',
    isLoading: status === 'loading',
    login,
    register,
    logout,
    refreshSession,
  }
}

export type { User }
