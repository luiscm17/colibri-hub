import { useState, type ReactNode } from 'react'
import {
  captureAdministrationOrigin,
  recoverAdministrationRoute,
  resolveDiscard,
  type AdministrationRecoveryReason,
  type AdministrationRouteState,
} from './route-state'

type AdministrationShellProps = Readonly<{
  route: AdministrationRouteState
  navigate(route: AdministrationRouteState): void
  children: (state: {
    route: AdministrationRouteState
    beginDraft(): void
    discardDraft(confirmed: boolean): void
    recover(reason: AdministrationRecoveryReason): void
  }) => ReactNode
}>

export function AdministrationShell({ route, navigate, children }: AdministrationShellProps) {
  const [origin, setOrigin] = useState<AdministrationRouteState | null>(null)

  const beginDraft = () => setOrigin(captureAdministrationOrigin(route))
  const discardDraft = (confirmed: boolean) => {
    if (!origin) return
    const result = resolveDiscard(origin, confirmed)
    if (result.action === 'restore') {
      navigate(result.route)
      setOrigin(null)
    }
  }

  return children({
    route,
    beginDraft,
    discardDraft,
    recover: (reason) => navigate(recoverAdministrationRoute(route, reason)),
  })
}
