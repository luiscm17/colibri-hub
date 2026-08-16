import { createContext, useContext } from 'react'
import type { AccessSnapshot, AccessState } from './access-controller'

export interface AccessContextValue {
  state: AccessState
  snapshot: AccessSnapshot | null
  refresh(): Promise<void>
  retry(): Promise<void>
  clear(): void
}

export const AccessContext = createContext<AccessContextValue | null>(null)

export function useAccess(): AccessContextValue {
  const context = useContext(AccessContext)
  if (!context) throw new Error('useAccess must be used within AccessProvider')
  return context
}
