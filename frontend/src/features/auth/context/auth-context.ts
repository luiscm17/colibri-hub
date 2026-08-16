import { createContext, useContext } from 'react'
import type {
  AuthenticationState,
  AuthenticationAccountSummary,
} from '../model/authenticationState'

export interface AuthContextValue {
  authState: AuthenticationState
  account: AuthenticationAccountSummary | null
  isAuthenticated: boolean
  accessHandoff: AuthenticationAccessHandoff
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  revalidate: () => Promise<void>
}

export type AuthenticationAccessHandoff =
  | { condition: 'unresolved' | 'password-change-required' | 'ended' }
  | { condition: 'unavailable'; retryable: boolean }
  | { condition: 'eligible'; accountId: string; handoffId: string }

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
