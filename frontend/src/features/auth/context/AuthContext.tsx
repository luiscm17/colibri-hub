import { useReducer, useEffect, useCallback, useMemo, useRef, type ReactNode } from 'react'
import { AuthContext } from './auth-context'
import type {
  AuthenticationState,
  AuthenticationAccountSummary,
} from '../model/authenticationState'
import { setTokenAccessor, clearTokenAccessor } from '@/api/httpClient'
import * as providerSession from '../provider/providerSession'
import { fetchCurrentAuthentication, mapToAccountSummary, terminateSession } from '../api/authApi'
import { isApiError } from '@/api/httpError'

type Action =
  | { type: 'SESSION_RESTORED'; account: AuthenticationAccountSummary }
  | { type: 'PASSWORD_CHANGE_REQUIRED'; account: AuthenticationAccountSummary }
  | { type: 'UNAUTHENTICATED'; reason?: 'logged-out' | 'expired' | 'denied' }
  | { type: 'UNAVAILABLE'; retryable: boolean }

function reducer(_state: AuthenticationState, action: Action): AuthenticationState {
  switch (action.type) {
    case 'SESSION_RESTORED':
      return { status: 'authenticated', account: action.account }
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

  const validateAccount = useCallback(async (): Promise<void> => {
    try {
      const response = await fetchCurrentAuthentication()
      const account = mapToAccountSummary(response)

      if (!mountedRef.current) return

      if (response.next_step === 'change_password') {
        dispatch({ type: 'PASSWORD_CHANGE_REQUIRED', account })
      } else {
        dispatch({ type: 'SESSION_RESTORED', account })
      }
    } catch (error) {
      if (!mountedRef.current) return

      if (isApiError(error)) {
        if (error.status === 401 || error.status === 403) {
          await providerSession.signOut()
          dispatch({ type: 'UNAUTHENTICATED', reason: 'denied' })
          return
        }
        if (error.kind === 'network') {
          dispatch({ type: 'UNAVAILABLE', retryable: true })
          return
        }
      }
      dispatch({ type: 'UNAUTHENTICATED', reason: 'denied' })
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true

    setTokenAccessor(providerSession.getAccessToken)

    async function initialize() {
      const active = await providerSession.hasSession()
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
        dispatch({ type: 'UNAUTHENTICATED', reason })
      } else if (event === 'TOKEN_REFRESHED') {
        // Token accessor already returns fresh token — no action needed
      }
    })

    return () => {
      mountedRef.current = false
      subscription.unsubscribe()
      clearTokenAccessor()
    }
  }, [validateAccount])

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
    await providerSession.signOut()
    dispatch({ type: 'UNAUTHENTICATED', reason: 'logged-out' })
  }, [])

  const revalidate = useCallback(async (): Promise<void> => {
    await validateAccount()
  }, [validateAccount])

  const account: AuthenticationAccountSummary | null =
    authState.status === 'authenticated' || authState.status === 'password-change-required'
      ? authState.account
      : null

  const isAuthenticated = authState.status === 'authenticated'

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const isResourceAllowed = useCallback((_resourceType: string): boolean => {
    // Stub: returns true until Access Control is implemented
    return true
  }, [])

  const value = useMemo(
    () => ({
      authState,
      account,
      isAuthenticated,
      isResourceAllowed,
      login,
      logout,
      revalidate,
    }),
    [authState, account, isAuthenticated, isResourceAllowed, login, logout, revalidate],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
