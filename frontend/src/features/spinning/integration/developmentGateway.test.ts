import { describe, expect, it } from 'vitest'
import { developmentSpinningGateway } from './developmentGateway'

describe('developmentSpinningGateway', () => {
  it('exposes local reference shapes and an ordered authorized Sample profile without server conclusions', async () => {
    const [catalog, profiles, continuity] = await Promise.all([
      developmentSpinningGateway.getProductionDischargeCatalog({ section: 'preparation', businessDate: '', shift: '' }),
      developmentSpinningGateway.getQualityProfiles({ sectionId: 'ring-spinning', businessDate: '2026-09-01', shiftId: 'A', inspectorId: 'inspector-1', machineId: '', yarnCountId: '' }),
      developmentSpinningGateway.getProgressContinuity({ section: 'preparation', businessDate: '', shift: '', machineId: 'FIN-01', yarnCountId: '30-1' }),
    ])

    expect(catalog.status).toBe('populated')
    expect(profiles).toMatchObject({ status: 'populated' })
    expect(continuity.status).toBe('unavailable')
    if (profiles.status !== 'populated') throw new Error('Expected local quality profiles.')

    const sample = profiles.data.find(profile => profile.method === 'sample')
    expect(sample?.label).toBe('Muestra autorizada')
    if (!sample || sample.method !== 'sample') throw new Error('Expected authorized Sample profile.')

    expect(sample.measurements).toHaveLength(12)
    expect(sample.measurements.map(measurement => measurement.label)).toEqual([
      'Título', 'Resistencia', 'Elongación', 'Regularidad', 'Imperfecciones finas', 'Imperfecciones gruesas',
      'Neps', 'Vellosidad', 'Torsión', 'Humedad', 'Masa', 'Color',
    ])
    expect(sample.measurements.every(measurement => measurement.serverResult === null)).toBe(true)
    expect(sample.measurements.every(measurement => ['pending', 'unavailable'].includes(measurement.toleranceStatus))).toBe(true)
    expect(sample.captureContext).toMatchObject({ machine: 'required', yarnCount: 'optional', applicableMachineIds: ['FIN-01', 'FIN-02'] })
  })
})
