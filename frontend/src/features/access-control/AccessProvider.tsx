import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { httpJson } from '@/api/httpClient'
import { useAuth } from '@/features/auth'
import { AccessController, type AccessState } from './access-controller'
import { AccessContext, type AccessContextValue } from './access-context'

export function AccessProvider({ children }: { children: ReactNode }) {
  const { accessHandoff } = useAuth()
  const [controller] = useState(() => new AccessController((signal) => httpJson('/access/me', { signal })))
  const [state, setState] = useState<AccessState>(() => controller.getState())

  useEffect(() => controller.subscribe(setState), [controller])
  useEffect(() => {
    void controller.acceptHandoff(accessHandoff)
  }, [accessHandoff, controller])
  useEffect(() => () => controller.clear(), [controller])

  const value = useMemo<AccessContextValue>(() => ({
    state,
    snapshot: state.status === 'ready' ? state.snapshot : null,
    refresh: () => controller.refresh(),
    retry: () => controller.retry(),
    clear: () => controller.clear(),
  }), [controller, state])

  return <AccessContext.Provider value={value}>{children}</AccessContext.Provider>
}
