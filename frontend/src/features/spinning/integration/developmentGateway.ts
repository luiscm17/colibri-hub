import type { ProductionDischargeCatalog, QualityCaptureCatalog, QualityProfile, QualitySampleRecord, RemoteState, SpinningGateway } from './contracts'
import { unavailableIntegrationState } from './unavailableGateway'

const catalog: ProductionDischargeCatalog = {
  machines: [
    { id: 'FIN-01', label: 'Continua 01' },
    { id: 'FIN-02', label: 'Continua 02' },
    { id: 'MAD-01', label: 'Madejera 01' },
  ],
  applicableMachineIds: ['FIN-01', 'FIN-02', 'MAD-01'],
  rovingTitleApplicableMachineIds: ['FIN-01', 'FIN-02'],
  yarnCounts: [
    { id: '20-1', label: '20/1' },
    { id: '30-1', label: '30/1' },
    { id: '40-1', label: '40/1' },
  ],
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

export const developmentSpinningGateway: SpinningGateway = {
  defaultQualityCaptureContext: {
    businessDate: '2026-09-01',
    shiftId: 'A',
    supervisorId: 'junior',
    analystId: 'pablo',
  },
  getIntegrationState: async () => unavailableIntegrationState,
  getSectionContext: async () => unavailableIntegrationState,
  getProductionDischargeCatalog: async () => ({ status: 'populated', data: catalog }),
  getProgressContinuity: async () => unavailableIntegrationState,
  getQualityCaptureCatalog: async () => ({ status: 'populated', data: qualityCaptureCatalog }),
  getQualityProfiles: async (context) => context.businessDate && context.shiftId && context.supervisorId && context.analystId ? qualityProfiles : { status: 'empty' },
  getQualitySampleRecords: async (profileId) => profileId === 'authorized-sample' ? { status: 'populated', data: sampleRecords } : { status: 'empty' },
}
