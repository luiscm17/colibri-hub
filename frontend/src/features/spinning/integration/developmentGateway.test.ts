import { describe, expect, it } from 'vitest'
import { developmentSpinningGateway } from './developmentGateway'

describe('developmentSpinningGateway', () => {
  it('exposes local reference shapes and an ordered authorized Sample profile without server conclusions', async () => {
    expect(developmentSpinningGateway.defaultQualityCaptureContext).toEqual({
      businessDate: '2026-09-01',
      shiftId: 'A',
      supervisorId: 'junior',
      analystId: 'pablo',
    })

    const [catalog, profiles, continuity] = await Promise.all([
      developmentSpinningGateway.getProductionDischargeCatalog({ section: 'preparation', businessDate: '', shift: '' }),
      developmentSpinningGateway.getQualityProfiles({ businessDate: '2026-09-01', shiftId: 'A', supervisorId: 'junior', analystId: 'pablo' }),
      developmentSpinningGateway.getProgressContinuity({ section: 'preparation', businessDate: '', shift: '', machineId: 'FIN-01', yarnCountId: '30-1' }),
    ])

    expect(catalog.status).toBe('populated')
    expect(profiles).toMatchObject({ status: 'populated' })
    expect(continuity.status).toBe('unavailable')
    if (profiles.status !== 'populated') throw new Error('Expected local quality profiles.')

    const sample = profiles.data.find(profile => profile.method === 'sample')
    expect(sample?.label).toBe('Muestra autorizada')
    if (!sample || sample.method !== 'sample') throw new Error('Expected authorized Sample profile.')

    expect(sample.sampleCount).toBe(12)
    expect(sample.resultColumns.map(column => column.label)).toEqual(['Promedio', 'Error STD', 'Cuerpo', 'km', 'No Cortes', 'Porcentaje %', 'CP', 'Empalmes'])
    expect(sample.supportsObservations).toBe(true)

    const records = await developmentSpinningGateway.getQualitySampleRecords(sample.id, { businessDate: '2026-09-01', shiftId: 'A', supervisorId: 'junior', analystId: 'pablo' })
    expect(records).toMatchObject({ status: 'populated' })
    if (records.status !== 'populated') throw new Error('Expected local sample records.')
    expect(records.data[0]).toMatchObject({ section: 'Preparación A', machine: 'PSJ-0A', type: 'HB', yarnTitle: '2/40' })
    expect(records.data[0].samples).toHaveLength(12)
    expect(records.data[0].projections.average).toBeNull()
  })
})
