import { httpJson } from '@/api/httpClient'
import type { AuthMeResponse, PasswordChangeRequest, PasswordChangeResponse } from './authApi.types'
import type { AuthenticationAccountSummary } from '../model/authenticationState'

export async function fetchCurrentAuthentication(): Promise<AuthMeResponse> {
  return httpJson<AuthMeResponse>('/auth/me')
}

export async function submitPasswordChange(
  currentPassword: string,
  newPassword: string,
): Promise<PasswordChangeResponse> {
  const body: PasswordChangeRequest = {
    current_password: currentPassword,
    new_password: newPassword,
  }
  return httpJson<PasswordChangeResponse>('/auth/password-change', {
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
    initials: response.initials,
    version: response.version,
  }
}
