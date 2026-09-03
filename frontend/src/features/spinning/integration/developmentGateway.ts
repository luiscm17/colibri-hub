import type { CorrectionContext, CorrectionHistoricalRecord, DashboardFilters, DashboardProjection, ProductionDischargeCatalog, QualityCaptureCatalog, QualityProfile, QualitySampleRecord, RemoteState, SpinningGateway, WasteCaptureCatalog } from './contracts'
import { unavailableIntegrationState } from './unavailableGateway'

const catalog: ProductionDischargeCatalog = {
  productionRoster: [
    { id: 'production-1', number: 1, machine: 'Continua 01', yarnTitle: '20/1', type: 'Algodón', defaultPackageTareWeightKg: '', defaultCartWeightKg: '', projections: { netWeightKg: null } },
    { id: 'production-2', number: 2, machine: 'Continua 02', yarnTitle: '30/1', type: 'Algodón', defaultPackageTareWeightKg: '', defaultCartWeightKg: '', projections: { netWeightKg: null } },
    { id: 'production-3', number: 3, machine: 'Madejera 01', yarnTitle: '40/1', type: 'Madeja', defaultPackageTareWeightKg: '', defaultCartWeightKg: '', projections: { netWeightKg: null } },
  ],
  progressRoster: [
    { id: 'progress-1', number: 1, machine: 'Continua 01', yarnTitle: '20/1', type: 'Algodón', projections: { continuity: null } },
    { id: 'progress-2', number: 2, machine: 'Continua 02', yarnTitle: '30/1', type: 'Algodón', projections: { continuity: null } },
  ],
}

const preparationCatalog: ProductionDischargeCatalog = {
  productionRoster: [
    { id: 'fin-01', number: 1, machine: 'FIN-01', yarnTitle: '', type: 'Finisor', defaultPackageTareWeightKg: '0', defaultCartWeightKg: '0', projections: { netWeightKg: null } },
    { id: 'fin-02', number: 2, machine: 'FIN-02', yarnTitle: '', type: 'Finisor', defaultPackageTareWeightKg: '0', defaultCartWeightKg: '0', projections: { netWeightKg: null } },
  ],
  progressRoster: [],
}

const qualityProfiles: RemoteState<readonly QualityProfile[]> = {
  status: 'populated',
  data: [{ id: 'authorized-sample', label: 'Muestra autorizada', method: 'sample', sampleCount: 12, resultColumns: [{ id: 'average', label: 'Promedio' }, { id: 'std-error', label: 'Error STD' }, { id: 'body', label: 'Cuerpo' }, { id: 'km', label: 'km' }, { id: 'cuts', label: 'No Cortes' }, { id: 'percentage', label: 'Porcentaje %' }, { id: 'cp', label: 'CP' }, { id: 'splices', label: 'Empalmes' }], supportsObservations: true }],
}

const sampleRecords: readonly QualitySampleRecord[] = [
  { id: 'quality-1', number: 1, section: 'Preparación A', machine: 'PSJ-0A', type: 'HB', yarnTitle: '2/40', samples: ['22,45', '22,35', '22,58', '22,03', '21,80', '21,78', '22,06', '22,80', '22,90', '21,45', '22,59', '22,23'], projections: { average: null, 'std-error': null, body: null, km: null, cuts: null, percentage: null, cp: null, splices: null }, observations: '' },
  { id: 'quality-2', number: 2, section: 'Preparación A', machine: 'PSJ-2A', type: 'HB', yarnTitle: '2/24', samples: [], projections: { average: null, 'std-error': null, body: null, km: null, cuts: null, percentage: null, cp: null, splices: null }, observations: '' },
]

const qualityCaptureCatalog: QualityCaptureCatalog = {
  shifts: [{ id: 'A', label: 'Turno A' }, { id: 'B', label: 'Turno B' }],
  supervisors: [{ id: 'junior', label: 'JUNIOR' }],
  analysts: [{ id: 'pablo', label: 'PABLO' }],
}

const wasteCaptureCatalog: WasteCaptureCatalog = {
  context: {
    shift: 'A',
    supervisor: 'JUNIOR',
    businessDate: '2026-05-03',
    recorder: 'RICHARD',
  },
  rows: [
    { id: 'quality-control', number: 1, section: 'Control de Calidad', machine: 'Control de Calidad', weightKg: '' },
    { id: 'preparation-passage-a', number: 2, section: 'Preparación', machine: 'Pasaje A', weightKg: '' },
    { id: 'preparation-finisher-a', number: 3, section: 'Preparación', machine: 'Finisor A', weightKg: '' },
    { id: 'preparation-passage-b', number: 4, section: 'Preparación', machine: 'Pasaje B', weightKg: '' },
    { id: 'preparation-finisher-b', number: 5, section: 'Preparación', machine: 'Finisor B', weightKg: '' },
    { id: 'ring-0a-1a', number: 6, section: 'Continuas', machine: 'CONT-0A, CONT-0B, CONT-1A', weightKg: '' },
    { id: 'ring-1b-2b', number: 7, section: 'Continuas', machine: 'CONT-1B, CONT-2A, CONT-2B', weightKg: '' },
    { id: 'ring-3a-3b', number: 8, section: 'Continuas', machine: 'CONT-3A, CONT-3B', weightKg: '' },
    { id: 'ring-4a-4b', number: 9, section: 'Continuas', machine: 'CONT-4A, CONT-4B', weightKg: '' },
    { id: 'ring-5a-6a', number: 10, section: 'Continuas', machine: 'CONT-5A, CONT-5B, CONT-6A', weightKg: '' },
    { id: 'ring-6b-7b', number: 11, section: 'Continuas', machine: 'CONT-6B, CONT-7A, CONT-7B', weightKg: '' },
    { id: 'ring-8a-9a', number: 12, section: 'Continuas', machine: 'CONT-8A, CONT-8B, CONT-9A', weightKg: '' },
    { id: 'ring-9b-10b', number: 13, section: 'Continuas', machine: 'CONT-9B, CONT-10A, CONT-10B', weightKg: '' },
    { id: 'ring-11a-11b', number: 14, section: 'Continuas', machine: 'CONT-11A, CONT-11B', weightKg: '' },
    { id: 'ring-12a-12b', number: 15, section: 'Continuas', machine: 'CONT-12A, CONT-12B', weightKg: '' },
    { id: 'ring-13a-13b', number: 16, section: 'Continuas', machine: 'CONT-13A, CONT-13B', weightKg: '' },
    { id: 'ring-other', number: 17, section: 'Continuas', machine: 'Otros', weightKg: '' },
    { id: 'bobbin-1', number: 18, section: 'Bobinados', machine: 'AUTCNR-1', weightKg: '' },
    { id: 'bobbin-2', number: 19, section: 'Bobinados', machine: 'AUTCNR-2', weightKg: '' },
    { id: 'bobbin-3', number: 20, section: 'Bobinados', machine: 'CNR-3', weightKg: '' },
    { id: 'bobbin-4', number: 21, section: 'Bobinados', machine: 'CNR-4', weightKg: '' },
    { id: 'bobbin-5', number: 22, section: 'Bobinados', machine: 'AUTCNR-5', weightKg: '' },
    { id: 'bobbin-6', number: 23, section: 'Bobinados', machine: 'CNR-6', weightKg: '' },
    { id: 'coupling-1a-2a', number: 24, section: 'Acoplado', machine: 'ACOP-1A, ACOP-2A', weightKg: '' },
    { id: 'coupling-1b-2b', number: 25, section: 'Acoplado', machine: 'ACOP-1B, ACOP-2B', weightKg: '' },
    { id: 'coupling-3', number: 26, section: 'Acoplado', machine: 'ACOP-3', weightKg: '' },
    { id: 'coupling-4', number: 27, section: 'Acoplado', machine: 'ACOP-4', weightKg: '' },
    { id: 'twisting-1a-2a', number: 28, section: 'Retorcido', machine: 'RET-1A, RET-1B, RET-2A', weightKg: '' },
    { id: 'twisting-2b-3a', number: 29, section: 'Retorcido', machine: 'RET-2B, RET-3A', weightKg: '' },
    { id: 'twisting-3b-4b', number: 30, section: 'Retorcido', machine: 'RET-3B, RET-4A, RET-4B', weightKg: '' },
    { id: 'twisting-5a-5b', number: 31, section: 'Retorcido', machine: 'RET-5A, RET-5B', weightKg: '' },
    { id: 'twisting-6a-6b', number: 32, section: 'Retorcido', machine: 'RET-6A, RET-6B', weightKg: '' },
    { id: 'twisting-7a-8b', number: 33, section: 'Retorcido', machine: 'RET-7A, RET-7B, RET-8A, RET-8B', weightKg: '' },
    { id: 'twisting-9a-9b', number: 34, section: 'Retorcido', machine: 'RET-9A, RET-9B', weightKg: '' },
    { id: 'skeining', number: 35, section: 'Madejera', machine: 'Madejera', weightKg: '' },
    { id: 'winding', number: 36, section: 'Devanado', machine: 'Devanado', weightKg: '' },
    { id: 'other', number: 37, section: 'OTROS', machine: 'Otros', weightKg: '' },
  ],
  totalKg: null,
}

const reportingProjection: DashboardProjection = {
  sections: [
    { section: 'Preparación', metrics: [{ name: 'total_discharged_kg', value: '1240.50', unit: 'kg', availability: 'available' }, { name: 'discharge_count', value: '18', unit: 'count', availability: 'available' }, { name: 'real_waste_kg', value: null, unit: 'kg', availability: 'unavailable', reason: 'El servicio aún no confirmó este indicador.' }] },
    { section: 'Continuas', metrics: [{ name: 'total_discharged_kg', value: '980.00', unit: 'kg', availability: 'available' }, { name: 'net_process_production_kg', value: '1012.00', unit: 'kg', availability: 'available' }, { name: 'real_waste_kg', value: '0', unit: 'kg', availability: 'zero' }] },
    { section: 'Bobinados', metrics: [{ name: 'average_discharge_kg', value: null, unit: 'kg', availability: 'not_applicable', reason: 'No hay una proyección aplicable para este período.' }] },
  ],
}

const correctionRecords: readonly CorrectionHistoricalRecord[] = [
  { family: 'production_discharge', recordId: 'discharge-1', section: 'Continuas', businessDate: '2026-09-01', shift: 'A', machine: 'Continua 01', dischargedKg: '120 kg' },
  { family: 'skeining_production', recordId: 'skeining-1', section: 'Madejeras', businessDate: '2026-09-01', shift: 'A', skeinMachine: 'Madejera 01', skeins: '48' },
  { family: 'progress', recordId: 'progress-1', section: 'Continuas', businessDate: '2026-09-01', shift: 'A', machine: 'Continua 01', outputKg: '12 kg' },
  { family: 'process_quality', recordId: 'quality-1', businessDate: '2026-09-01', shift: 'A', profile: 'Muestra autorizada', sample: 'PSJ-0A', result: '22,45' },
  { family: 'waste', recordId: 'waste-1', businessDate: '2026-09-01', shift: 'A', area: 'Continuas', wasteKg: '4 kg' },
]

const readCorrectionContext = (context: CorrectionContext) => ({ status: 'populated' as const, data: { context, records: correctionRecords.filter(record => record.businessDate === context.businessDate && record.shift === context.shift && (!('section' in record) || record.section === context.section)), progressContinuityWarning: 'Revise la continuidad con el registro anterior.' } })

function getDevelopmentDashboard(_filters: DashboardFilters, section: string | null): RemoteState<DashboardProjection> {
  if (!section) return { status: 'populated', data: reportingProjection }
  return { status: 'populated', data: { sections: reportingProjection.sections.filter(item => item.section === section) } }
}

export const developmentSpinningGateway: SpinningGateway = {
  defaultQualityCaptureContext: {
    businessDate: '2026-09-01',
    shiftId: 'A',
    supervisorId: 'junior',
    analystId: 'pablo',
  },
  getIntegrationState: async () => unavailableIntegrationState,
  getSectionContext: async () => unavailableIntegrationState,
  getProductionDischargeCatalog: async (identity) => ({ status: 'populated', data: identity.section === 'preparation' ? preparationCatalog : catalog }),
  getProgressContinuity: async () => unavailableIntegrationState,
  getQualityCaptureCatalog: async () => ({ status: 'populated', data: qualityCaptureCatalog }),
  getQualityProfiles: async (context) => context.businessDate && context.shiftId && context.supervisorId && context.analystId ? qualityProfiles : { status: 'empty' },
  getQualitySampleRecords: async (profileId) => profileId === 'authorized-sample' ? { status: 'populated', data: sampleRecords } : { status: 'empty' },
  getWasteCaptureCatalog: async () => ({ status: 'populated', data: wasteCaptureCatalog }),
  getDashboard: async (filters, section) => getDevelopmentDashboard(filters, section),
  corrections: {
    readCorrectionContext: async context => readCorrectionContext(context),
    saveCorrectionContext: async draft => readCorrectionContext(draft.context),
  },
}
