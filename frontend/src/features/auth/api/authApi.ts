import { httpJson } from '@/api/httpClient'
import { ApiError } from '@/api/httpError'
import type {
  AuthMeResponse,
  AuthenticationAccountResponse,
  DisableAccountRequest,
  EnableAccountRequest,
  PasswordChangeRequest,
  ProvisionAccountRequest,
  ProvisionAccountResponse,
  ResetPasswordRequest,
} from './authApi.types'
import type { AuthenticationAccountSummary } from '../model/authenticationState'

export async function fetchCurrentAuthentication(): Promise<AuthMeResponse> {
  const response = await httpJson<unknown>('/auth/me')
  if (!isAuthMeResponse(response)) {
    throw new ApiError({
      kind: 'invalid_response',
      message: 'The server returned an invalid authentication response.',
    })
  }
  return response
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

export async function fetchAuthenticationAccounts(): Promise<AuthenticationAccountResponse[]> {
  const response = await httpJson<unknown>('/auth/accounts')
  if (!Array.isArray(response) || !response.every(isAuthenticationAccountResponse)) {
    throw invalidAuthenticationResponse()
  }
  return response
}

export async function fetchAuthenticationAccount(accountId: string): Promise<AuthenticationAccountResponse> {
  const response = await httpJson<unknown>(`/auth/accounts/${encodeURIComponent(accountId)}`)
  if (!isAuthenticationAccountResponse(response)) {
    throw invalidAuthenticationResponse()
  }
  return response
}

export async function provisionAuthenticationAccount(
  body: ProvisionAccountRequest,
): Promise<ProvisionAccountResponse> {
  const response = await httpJson<unknown>('/auth/accounts', { method: 'POST', body })
  if (!isAuthenticationAccountResponse(response)) {
    throw invalidAuthenticationResponse()
  }
  return response
}

export async function resetAuthenticationAccountPassword(
  accountId: string,
  body: ResetPasswordRequest,
): Promise<void> {
  return expectNoContent(`/auth/accounts/${encodeURIComponent(accountId)}/password-reset`, body)
}

export async function disableAuthenticationAccount(
  accountId: string,
  body: DisableAccountRequest,
): Promise<void> {
  return expectNoContent(`/auth/accounts/${encodeURIComponent(accountId)}/disable`, body)
}

export async function enableAuthenticationAccount(
  accountId: string,
  body: EnableAccountRequest,
): Promise<void> {
  return expectNoContent(`/auth/accounts/${encodeURIComponent(accountId)}/enable`, body)
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

function isAuthMeResponse(value: unknown): value is AuthMeResponse {
  if (!isRecord(value)) return false
  return isString(value.account_id)
    && isString(value.email)
    && isString(value.display_name)
    && isString(value.status)
    && (value.next_step === 'change_password' || value.next_step === 'load_access')
}

function isAuthenticationAccountResponse(value: unknown): value is AuthenticationAccountResponse {
  if (!isRecord(value)) return false
  return isString(value.account_id)
    && isString(value.email)
    && isString(value.display_name)
    && isString(value.user_code)
    && isString(value.status)
    && isNonNegativeInteger(value.version)
}

async function expectNoContent(path: string, body: unknown): Promise<void> {
  const response = await httpJson<unknown>(path, { method: 'POST', body })
  if (response !== undefined) {
    throw invalidAuthenticationResponse()
  }
}

function invalidAuthenticationResponse(): ApiError {
  return new ApiError({
    kind: 'invalid_response',
    message: 'The server returned an invalid authentication response.',
  })
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isString(value: unknown): value is string {
  return typeof value === 'string'
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0
}
