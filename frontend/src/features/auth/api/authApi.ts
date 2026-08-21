import { httpJson } from '@/api/httpClient'
import type { AuthMeResponse, PasswordChangeRequest } from './authApi.types'
import type { AuthenticationAccountSummary } from '../model/authenticationState'

export async function fetchCurrentAuthentication(): Promise<AuthMeResponse> {
  return httpJson<AuthMeResponse>('/auth/me')
}

export async function submitPasswordChange(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  const body: PasswordChangeRequest = {
    current_password: currentPassword,
    new_password: newPassword,
  }
  return httpJson<void>('/auth/password-change', {
    method: 'POST',
    body,
  })
}

export async function terminateSession(): Promise<void> {
  return httpJson<void>('/auth/session', { method: 'DELETE' })
}

export function mapToAccountSummary(response: AuthMeResponse): AuthenticationAccountSummary {
  return {
    accountId: response.account_id,
    email: response.email,
    displayName: response.display_name,
    initials: deriveInitials(response.display_name),
  }
}

function deriveInitials(displayName: string): string {
  const words = displayName.trim().split(/\s+/).filter(Boolean)
  return words.slice(0, 2).map((word) => word.charAt(0).toUpperCase()).join('') || '?'
}
