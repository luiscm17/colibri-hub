import type { AdministrationFamily } from './operations'

export type AdministrationRouteState = Readonly<{
  family: AdministrationFamily
  criteria: Readonly<Record<string, string>>
  page: number
  subjectId?: string
}>

export type AdministrationRecoveryReason = 'stale' | 'invalid' | 'empty-page'

export function captureAdministrationOrigin(route: AdministrationRouteState): AdministrationRouteState {
  return { ...route, criteria: { ...route.criteria } }
}

export function resolveDiscard(
  origin: AdministrationRouteState,
  confirmed: boolean,
): { action: 'preserve' } | { action: 'restore'; route: AdministrationRouteState } {
  return confirmed ? { action: 'restore', route: captureAdministrationOrigin(origin) } : { action: 'preserve' }
}

export function recoverAdministrationRoute(
  route: AdministrationRouteState,
  reason: AdministrationRecoveryReason,
): AdministrationRouteState {
  if (reason === 'empty-page' && route.page > 1) return { ...route, page: route.page - 1 }
  if (reason === 'stale' || reason === 'invalid') {
    return { family: route.family, criteria: { ...route.criteria }, page: route.page }
  }
  return route
}
