import { create } from 'zustand'
import type { User } from '../types/auth'
import { registerAccount, signIn, signOut, getCurrentSession } from '../services/authService'
import { useInterviewStore } from './interviewStore'
import { toErrorMessage } from '../utils/errorHandler'

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthStore {
  status: AuthStatus
  user: User | null
  lastUserId: string | null
  error: string | null
  refreshSession: () => Promise<void>
  register: (email: string, password: string) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  status: 'loading',
  user: null,
  lastUserId: null,
  error: null,

  // Probe the HTTP-only session cookie on boot. The server answers {user: null}
  // instead of 401 so this never logs a noisy error for guests.
  refreshSession: async () => {
    try {
      const user = await getCurrentSession()
      set({ status: user ? 'authenticated' : 'unauthenticated', user, error: null })
    } catch {
      set({ status: 'unauthenticated', user: null, error: null })
    }
  },

  register: async (email, password) => {
    set({ error: null })
    try {
      const user = await registerAccount(email, password)
      const accountChanged = user.id !== get().lastUserId
      set({ status: 'authenticated', user, lastUserId: user.id, error: null })
      if (accountChanged) useInterviewStore.getState().reset()
    } catch (error) {
      set({ error: toErrorMessage(error) })
      throw error
    }
  },

  login: async (email, password) => {
    set({ error: null })
    try {
      const user = await signIn(email, password)
      const accountChanged = user.id !== get().lastUserId
      set({ status: 'authenticated', user, lastUserId: user.id, error: null })
      if (accountChanged) useInterviewStore.getState().reset()
    } catch (error) {
      set({ error: toErrorMessage(error) })
      throw error
    }
  },

  logout: async () => {
    try {
      await signOut()
    } finally {
      set({ status: 'unauthenticated', user: null, error: null })
    }
  },
}))
