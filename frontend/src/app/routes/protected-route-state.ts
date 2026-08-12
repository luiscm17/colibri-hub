import type { AccessRequirement, AccessState } from '@/features/access-control'

export type ProtectedRouteOutcome = 'loading' | 'allowed' | 'denied' | 'blocked' | 'unavailable'

export function resolveProtectedRoute(state: AccessState, requirement: AccessRequirement): ProtectedRouteOutcome {
  if (state.status === 'waiting-for-authentication' || state.status === 'loading') return 'loading'
  if (state.status === 'blocked') return 'blocked'
  if (state.status === 'unavailable') return 'unavailable'
  return state.snapshot.allows(requirement) ? 'allowed' : 'denied'
}
