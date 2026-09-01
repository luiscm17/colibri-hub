import type { ProductionDischargeCatalog, QualityCaptureCatalog, QualityMeasurement, QualityProfile, RemoteState, SpinningGateway } from './contracts'
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

const sampleMeasurements: readonly QualityMeasurement[] = [
  { id: 'title', label: 'Título', unit: 'Ne', required: true, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
  { id: 'strength', label: 'Resistencia', unit: 'cN/tex', required: true, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
  { id: 'elongation', label: 'Elongación', unit: '%', required: true, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
  { id: 'evenness', label: 'Regularidad', unit: 'CVm %', required: true, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
  { id: 'thin-places', label: 'Imperfecciones finas', unit: '−', required: false, validation: 'integer', serverResult: null, toleranceStatus: 'pending' },
  { id: 'thick-places', label: 'Imperfecciones gruesas', unit: '−', required: false, validation: 'integer', serverResult: null, toleranceStatus: 'pending' },
  { id: 'neps', label: 'Neps', unit: '−', required: false, validation: 'integer', serverResult: null, toleranceStatus: 'pending' },
  { id: 'hairiness', label: 'Vellosidad', unit: 'H', required: true, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
  { id: 'twist', label: 'Torsión', unit: 'vueltas/m', required: true, validation: 'integer', serverResult: null, toleranceStatus: 'pending' },
  { id: 'humidity', label: 'Humedad', unit: '%', required: true, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
  { id: 'mass', label: 'Masa', unit: 'g', required: false, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
  { id: 'color', label: 'Color', unit: 'grado', required: false, validation: 'text', serverResult: null, toleranceStatus: 'unavailable' },
]

const qualityProfiles: RemoteState<readonly QualityProfile[]> = {
  status: 'populated',
  data: [{ id: 'authorized-sample', label: 'Muestra autorizada', method: 'sample', captureContext: { machine: 'required', applicableMachineIds: ['FIN-01', 'FIN-02'], yarnCount: 'optional', applicableYarnCountIds: ['20-1', '30-1', '40-1'] }, measurements: sampleMeasurements }],
}

const qualityCaptureCatalog: QualityCaptureCatalog = {
  sections: [{ id: 'ring-spinning', label: 'Continuas' }, { id: 'skeining', label: 'Madejeras' }],
  shifts: [{ id: 'A', label: 'Turno A' }, { id: 'B', label: 'Turno B' }],
  inspectors: [{ id: 'inspector-1', label: 'Inspector 1' }],
  machines: catalog.machines,
  yarnCounts: catalog.yarnCounts,
}

export const developmentSpinningGateway: SpinningGateway = {
  getIntegrationState: async () => unavailableIntegrationState,
  getSectionContext: async () => unavailableIntegrationState,
  getProductionDischargeCatalog: async () => ({ status: 'populated', data: catalog }),
  getProgressContinuity: async () => unavailableIntegrationState,
  getQualityCaptureCatalog: async () => ({ status: 'populated', data: qualityCaptureCatalog }),
  getQualityProfiles: async (context) => context.sectionId === 'ring-spinning' && context.businessDate && context.shiftId && context.inspectorId ? qualityProfiles : { status: 'empty' },
}
