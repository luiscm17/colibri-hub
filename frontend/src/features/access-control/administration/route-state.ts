import type { AdministrationFamily } from './operations'

export type AdministrationRouteState = Readonly<{
  family: AdministrationFamily
  criteria: Readonly<Record<string, string>>
  page: number
  subjectId?: string
  mode?: 'edit'
}>

export type AdministrationRecoveryReason = 'missing' | 'denied' | 'stale' | 'invalid' | 'aborted'

const ORIGIN_PARAM = '_origin'

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
  void reason
  return { family: route.family, criteria: { ...route.criteria }, page: route.page }
}

export function encodeAdministrationOrigin(origin: AdministrationRouteState): string {
  return JSON.stringify(captureAdministrationOrigin(origin))
}

export function decodeAdministrationOrigin(value: string | null): AdministrationRouteState | null {
  if (!value) return null
  try {
    const candidate = JSON.parse(value) as Partial<AdministrationRouteState>
    if (typeof candidate.family !== 'string' || !candidate.criteria || typeof candidate.criteria !== 'object' || !Number.isInteger(candidate.page) || candidate.page! < 1) return null
    return captureAdministrationOrigin(candidate as AdministrationRouteState)
  } catch {
    return null
  }
}

export { ORIGIN_PARAM }
