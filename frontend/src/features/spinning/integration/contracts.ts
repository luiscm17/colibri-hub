export type RemoteState<T> =
  | { status: 'loading' }
  | { status: 'unavailable'; message: string; retryable: boolean }
  | { status: 'failure'; message: string }
  | { status: 'empty' }
  | { status: 'populated'; data: T }
  | { status: 'stale'; data: T; message: string }
  | { status: 'conflict'; message: string }

export type SectionIdentity = Readonly<{ section: string; businessDate: string; shift: string }>

export type ReferenceOption = Readonly<{ id: string; label: string }>

export type ProductionDischargeCatalog = Readonly<{
  machines: readonly ReferenceOption[]
  applicableMachineIds: readonly string[]
  yarnCounts: readonly ReferenceOption[]
}>

export type ProgressContinuity =
  | { kind: 'predecessor'; predecessorInput: unknown; editableSuggestions: readonly unknown[] }
  | { kind: 'no-predecessor' }
  | { kind: 'stale-configuration'; message: string }

export interface SpinningGateway {
  getIntegrationState(signal?: AbortSignal): Promise<RemoteState<never>>
  getSectionContext(identity: SectionIdentity, signal?: AbortSignal): Promise<RemoteState<never>>
  getProductionDischargeCatalog(identity: SectionIdentity, signal?: AbortSignal): Promise<RemoteState<ProductionDischargeCatalog>>
  getProgressContinuity(identity: SectionIdentity, signal?: AbortSignal): Promise<RemoteState<ProgressContinuity>>
}
