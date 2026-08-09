import { fetchMe, loginUser, logoutUser, registerUser } from '../api/auth'
import type { User } from '../types/auth'

export async function registerAccount(email: string, password: string): Promise<User> {
  return registerUser({ email, password })
}

export async function signIn(email: string, password: string): Promise<User> {
  return loginUser({ email, password })
}

export async function signOut(): Promise<void> {
  await logoutUser()
}

export async function getCurrentSession(): Promise<User | null> {
  const me = await fetchMe()
  return me.user
}
