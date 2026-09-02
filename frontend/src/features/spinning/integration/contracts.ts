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

export type ProductionRosterEntry = Readonly<{
  id: string
  number: number
  machine: string
  yarnTitle: string
  type: string
  defaultPackageTareWeightKg: string
  defaultCartWeightKg: string
  projections: Readonly<Record<string, string | null>>
}>

export type ProgressRosterEntry = Readonly<{
  id: string
  number: number
  machine: string
  yarnTitle: string
  type: string
  projections: Readonly<Record<string, string | null>>
}>

export type ProductionDischargeCatalog = Readonly<{
  productionRoster: readonly ProductionRosterEntry[]
  progressRoster: readonly ProgressRosterEntry[]
}>

export type WasteCaptureCatalog = Readonly<{
  context: WasteCaptureContext
  rows: readonly WasteCaptureRecord[]
  totalKg: string | null
}>

export type WasteCaptureContext = Readonly<{
  shift: string
  supervisor: string
  businessDate: string
  recorder: string
}>

export type WasteCaptureRecord = Readonly<{
  id: string
  number: number
  section: string
  machine: string
  weightKg: string
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
  businessDate: string
  shiftId: string
  supervisorId: string
  analystId: string
}>

export type QualityCaptureCatalog = Readonly<{
  shifts: readonly ReferenceOption[]
  supervisors: readonly ReferenceOption[]
  analysts: readonly ReferenceOption[]
}>

export type QualitySampleProjectionColumn = Readonly<{
  id: string
  label: string
}>

export type QualitySampleRecord = Readonly<{
  id: string
  number: number
  section: string
  machine: string
  type: string
  yarnTitle: string
  samples: readonly string[]
  projections: Readonly<Record<string, string | null>>
  observations?: string
}>

export type QualityObservationProfile = Readonly<{
  id: string
  label: string
  method: 'observation'
  captureFields: readonly QualityCaptureField[]
}>

export type QualitySampleProfile = Readonly<{
  id: string
  label: string
  method: 'sample'
  sampleCount: number
  resultColumns: readonly QualitySampleProjectionColumn[]
  supportsObservations: boolean
}>

export type QualityProfile = QualityObservationProfile | QualitySampleProfile

export type DashboardMetricAvailability = 'available' | 'zero' | 'not_applicable' | 'unavailable'

export type DashboardMetric = Readonly<{
  name: string
  value: string | null
  unit: string | null
  availability: DashboardMetricAvailability
  reason?: string
}>

export type DashboardSection = Readonly<{
  section: string
  metrics: readonly DashboardMetric[]
}>

export type DashboardProjection = Readonly<{
  sections: readonly DashboardSection[]
}>

export type DashboardFilters = Readonly<{
  businessDateFrom: string
  businessDateTo: string
  shift: string
  machine: string
  machineGroup: string
  yarnCount: string
}>

export interface SpinningGateway {
  defaultQualityCaptureContext?: QualityCaptureContext
  getIntegrationState(signal?: AbortSignal): Promise<RemoteState<never>>
  getSectionContext(identity: SectionIdentity, signal?: AbortSignal): Promise<RemoteState<never>>
  getProductionDischargeCatalog(identity: SectionIdentity, signal?: AbortSignal): Promise<RemoteState<ProductionDischargeCatalog>>
  getProgressContinuity(identity: ProgressIdentity, signal?: AbortSignal): Promise<RemoteState<ProgressContinuity>>
  getQualityCaptureCatalog(signal?: AbortSignal): Promise<RemoteState<QualityCaptureCatalog>>
  getQualityProfiles(context: QualityCaptureContext, signal?: AbortSignal): Promise<RemoteState<readonly QualityProfile[]>>
  getQualitySampleRecords(profileId: string, context: QualityCaptureContext, signal?: AbortSignal): Promise<RemoteState<readonly QualitySampleRecord[]>>
  getWasteCaptureCatalog?(signal?: AbortSignal): Promise<RemoteState<WasteCaptureCatalog>>
  getDashboard?(filters: DashboardFilters, section: string | null, signal?: AbortSignal): Promise<RemoteState<DashboardProjection>>
}
