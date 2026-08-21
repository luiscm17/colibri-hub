export interface AuthenticationAccountSummary {
  accountId: string
  email: string
  displayName: string
  initials: string
}

export type UnauthenticatedReason = 'logged-out' | 'expired' | 'denied'

export type AuthenticationState =
  | { status: 'initializing' }
  | { status: 'unauthenticated'; reason?: UnauthenticatedReason }
  | { status: 'password-change-required'; account: AuthenticationAccountSummary }
  | { status: 'authenticated'; account: AuthenticationAccountSummary; handoffId: string }
  | { status: 'unavailable'; retryable: boolean }
