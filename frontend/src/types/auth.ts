export interface User {
  id: string
  email: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface MeResponse {
  user: User | null
}

export interface LogoutResponse {
  detail: string
}
