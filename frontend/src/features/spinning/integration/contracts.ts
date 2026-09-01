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
  rovingTitleApplicableMachineIds: readonly string[]
  yarnCounts: readonly ReferenceOption[]
}>

export type ProgressContinuity =
  | { kind: 'predecessor'; predecessorInput: unknown; editableSuggestions: readonly unknown[] }
  | { kind: 'no-predecessor' }
  | { kind: 'stale-configuration'; message: string }

export type ProgressIdentity = SectionIdentity & Readonly<{ machineId: string; yarnCountId: string }>

export type QualityCaptureField = Readonly<{
  id: string
  label: string
  required: boolean
}>

export type QualityCaptureContext = Readonly<{
  sectionId: string
  businessDate: string
  shiftId: string
  inspectorId: string
  machineId: string
  yarnCountId: string
}>

export type QualityCaptureCatalog = Readonly<{
  sections: readonly ReferenceOption[]
  shifts: readonly ReferenceOption[]
  inspectors: readonly ReferenceOption[]
  machines: readonly ReferenceOption[]
  yarnCounts: readonly ReferenceOption[]
}>

export type QualityProfileContext = Readonly<{
  machine: 'hidden' | 'optional' | 'required'
  applicableMachineIds: readonly string[]
  yarnCount: 'hidden' | 'optional' | 'required'
  applicableYarnCountIds: readonly string[]
}>

export type QualityMeasurement = Readonly<{
  id: string
  label: string
  unit: string
  required: boolean
  validation: 'decimal' | 'integer' | 'text'
  serverResult: string | null
  toleranceStatus: 'pending' | 'within-tolerance' | 'out-of-tolerance' | 'unavailable'
}>

export type QualityObservationProfile = Readonly<{
  id: string
  label: string
  method: 'observation'
  captureFields: readonly QualityCaptureField[]
}> & Readonly<{ captureContext: QualityProfileContext }>

export type QualitySampleProfile = Readonly<{
  id: string
  label: string
  method: 'sample'
  measurements: readonly QualityMeasurement[]
}> & Readonly<{ captureContext: QualityProfileContext }>

export type QualityProfile = QualityObservationProfile | QualitySampleProfile

export interface SpinningGateway {
  getIntegrationState(signal?: AbortSignal): Promise<RemoteState<never>>
  getSectionContext(identity: SectionIdentity, signal?: AbortSignal): Promise<RemoteState<never>>
  getProductionDischargeCatalog(identity: SectionIdentity, signal?: AbortSignal): Promise<RemoteState<ProductionDischargeCatalog>>
  getProgressContinuity(identity: ProgressIdentity, signal?: AbortSignal): Promise<RemoteState<ProgressContinuity>>
  getQualityCaptureCatalog(signal?: AbortSignal): Promise<RemoteState<QualityCaptureCatalog>>
  getQualityProfiles(context: QualityCaptureContext, signal?: AbortSignal): Promise<RemoteState<readonly QualityProfile[]>>
}
