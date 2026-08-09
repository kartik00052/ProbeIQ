import { apiClient } from './client'
import type {
  LoginRequest,
  LogoutResponse,
  MeResponse,
  RegisterRequest,
  User,
} from '../types/auth'

export async function registerUser(payload: RegisterRequest): Promise<User> {
  const { data } = await apiClient.post<User>('/auth/register', payload)
  return data
}

export async function loginUser(payload: LoginRequest): Promise<User> {
  const { data } = await apiClient.post<User>('/auth/login', payload)
  return data
}

export async function logoutUser(): Promise<LogoutResponse> {
  const { data } = await apiClient.post<LogoutResponse>('/auth/logout')
  return data
}

export async function fetchMe(): Promise<MeResponse> {
  const { data } = await apiClient.get<MeResponse>('/auth/me')
  return data
}
