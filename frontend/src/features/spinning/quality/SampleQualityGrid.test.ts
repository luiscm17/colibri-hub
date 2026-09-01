import { describe, expect, it } from 'vitest'
import { sampleMeasurementValidationError, sampleQualityRows } from './qualityModel'
import type { QualityMeasurement } from '../integration/contracts'

describe('SampleQualityGrid model', () => {
  const measurements: readonly QualityMeasurement[] = [
    { id: 'first', label: 'First', unit: 'u', required: true, validation: 'decimal', serverResult: '1,2', toleranceStatus: 'within-tolerance' },
    { id: 'second', label: 'Second', unit: 'u', required: false, validation: 'integer', serverResult: null, toleranceStatus: 'pending' },
  ]

  it('preserves profile order and server projections without deriving results', () => {
    expect(sampleQualityRows(measurements, { second: '2', first: '1,5' })).toMatchObject([
      { id: 'first', value: '1,5', serverResult: '1,2', toleranceStatus: 'within-tolerance' },
      { id: 'second', value: '2', serverResult: null, toleranceStatus: 'pending' },
    ])
  })

  it('validates only configured input formats and required values', () => {
    expect(sampleMeasurementValidationError({ required: true, validation: 'decimal', value: '' })).toContain('obligatoria')
    expect(sampleMeasurementValidationError({ required: false, validation: 'integer', value: '1,2' })).toContain('entero')
    expect(sampleMeasurementValidationError({ required: true, validation: 'decimal', value: '1,2' })).toBeUndefined()
  })
})
