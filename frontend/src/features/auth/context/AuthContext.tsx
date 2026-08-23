import { useReducer, useEffect, useCallback, useMemo, useRef, type ReactNode } from 'react'
import { AuthContext, type AuthenticationAccessHandoff } from './auth-context'
import type {
  AuthenticationState,
  AuthenticationAccountSummary,
} from '../model/authenticationState'
import { clearAuthenticationRequiredHandler, setAuthenticationRequiredHandler, setTokenAccessor, clearTokenAccessor } from '@/api/httpClient'
import * as providerSession from '../provider/providerSession'
import { fetchCurrentAuthentication, mapToAccountSummary, terminateSession } from '../api/authApi'
import { isApiError } from '@/api/httpError'

type Action =
  | { type: 'SESSION_RESTORED'; account: AuthenticationAccountSummary; handoffId: string }
  | { type: 'PASSWORD_CHANGE_REQUIRED'; account: AuthenticationAccountSummary }
  | { type: 'UNAUTHENTICATED'; reason?: 'logged-out' | 'expired' | 'denied' }
  | { type: 'UNAVAILABLE'; retryable: boolean }

function reducer(_state: AuthenticationState, action: Action): AuthenticationState {
  switch (action.type) {
    case 'SESSION_RESTORED':
      return { status: 'authenticated', account: action.account, handoffId: action.handoffId }
    case 'PASSWORD_CHANGE_REQUIRED':
      return { status: 'password-change-required', account: action.account }
    case 'UNAUTHENTICATED':
      return { status: 'unauthenticated', reason: action.reason }
    case 'UNAVAILABLE':
      return { status: 'unavailable', retryable: action.retryable }
  }
}

const INITIAL_STATE: AuthenticationState = { status: 'initializing' }

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, dispatch] = useReducer(reducer, INITIAL_STATE)
  const mountedRef = useRef(true)
  const logoutInitiatedRef = useRef(false)
  const validationEpochRef = useRef(0)

  const endLocalSession = useCallback((reason: 'logged-out' | 'expired' | 'denied'): void => {
    validationEpochRef.current += 1
    clearTokenAccessor()
    if (mountedRef.current) dispatch({ type: 'UNAUTHENTICATED', reason })
  }, [])

  const validateAccount = useCallback(async (): Promise<void> => {
    const validationEpoch = validationEpochRef.current
    try {
      const response = await fetchCurrentAuthentication()
      const account = mapToAccountSummary(response)

      if (!mountedRef.current || validationEpoch !== validationEpochRef.current) return

      if (response.next_step === 'change_password') {
        dispatch({ type: 'PASSWORD_CHANGE_REQUIRED', account })
      } else {
        dispatch({ type: 'SESSION_RESTORED', account, handoffId: crypto.randomUUID() })
      }
    } catch (error) {
      if (!mountedRef.current || validationEpoch !== validationEpochRef.current) return

      if (isApiError(error)) {
        if (error.status === 401 || error.status === 403) {
          endLocalSession(error.status === 401 ? 'expired' : 'denied')
          try {
            await providerSession.signOut()
          } catch {
            // Provider cleanup is best-effort after local session termination.
          }
          return
        }
        if (error.kind === 'network') {
          dispatch({ type: 'UNAVAILABLE', retryable: true })
          return
        }
      }
      dispatch({ type: 'UNAUTHENTICATED', reason: 'denied' })
    }
  }, [endLocalSession])

  useEffect(() => {
    mountedRef.current = true

    setTokenAccessor(providerSession.getAccessToken)
    setAuthenticationRequiredHandler(async () => {
      endLocalSession('expired')
      try {
        await providerSession.signOut()
      } catch {
        // Provider cleanup is best-effort after local session termination.
      }
    })

    async function initialize() {
      let active: boolean
      try {
        active = await providerSession.hasSession()
      } catch {
        if (mountedRef.current) dispatch({ type: 'UNAVAILABLE', retryable: true })
        return
      }
      if (!mountedRef.current) return

      if (!active) {
        dispatch({ type: 'UNAUTHENTICATED' })
        return
      }

      await validateAccount()
    }

    initialize()

    const subscription = providerSession.onAuthStateChange((event) => {
      if (!mountedRef.current) return

      if (event === 'SIGNED_OUT') {
        const reason = logoutInitiatedRef.current ? 'logged-out' : 'expired'
        logoutInitiatedRef.current = false
        endLocalSession(reason)
      } else if (event === 'TOKEN_REFRESHED') {
        // Token accessor already returns fresh token — no action needed
      }
    })

    return () => {
      mountedRef.current = false
      subscription.unsubscribe()
      clearAuthenticationRequiredHandler()
      clearTokenAccessor()
    }
  }, [endLocalSession, validateAccount])

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    const { error } = await providerSession.signIn(email, password)
    if (error) {
      throw new Error(error)
    }
    await validateAccount()
  }, [validateAccount])

  const logout = useCallback(async (): Promise<void> => {
    logoutInitiatedRef.current = true
    try {
      await terminateSession()
    } catch {
      // Best-effort backend notification — proceed with local cleanup
    }
    endLocalSession('logged-out')
    try {
      await providerSession.signOut()
    } catch {
      // Provider cleanup is best-effort after local session termination.
    }
  }, [endLocalSession])

  const revalidate = useCallback(async (): Promise<void> => {
    await validateAccount()
  }, [validateAccount])

  const account: AuthenticationAccountSummary | null =
    authState.status === 'authenticated' || authState.status === 'password-change-required'
      ? authState.account
      : null

  const isAuthenticated = authState.status === 'authenticated'

  const accessHandoff: AuthenticationAccessHandoff = (() => {
    if (authState.status === 'authenticated') {
      return { condition: 'eligible', accountId: authState.account.accountId, handoffId: authState.handoffId }
    }
    if (authState.status === 'unavailable') return { condition: 'unavailable', retryable: authState.retryable }
    if (authState.status === 'password-change-required') return { condition: 'password-change-required' }
    if (authState.status === 'initializing') return { condition: 'unresolved' }
    return { condition: 'ended' }
  })()

  const value = useMemo(
    () => ({
      authState,
      account,
      isAuthenticated,
      accessHandoff,
      login,
      logout,
      revalidate,
    }),
    [authState, account, isAuthenticated, accessHandoff, login, logout, revalidate],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
