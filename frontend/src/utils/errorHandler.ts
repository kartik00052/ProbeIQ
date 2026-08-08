import { AxiosError } from 'axios'
import type { ApiErrorBody } from '../types/api'

export function toErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const body = error.response?.data as ApiErrorBody | undefined
    if (body?.detail) return body.detail
    if (body?.error) return body.error
    if (error.message) return error.message
  }
  if (error instanceof Error) return error.message
  return 'Something went wrong. Please try again.'
}
