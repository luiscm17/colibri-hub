import { describe, expect, it } from 'vitest'
import { updateSampleRecord } from './qualityModel'
import type { QualitySampleRecord } from '../integration/contracts'

describe('SampleQualityGrid model', () => {
  const records: readonly QualitySampleRecord[] = [
    { id: 'first', number: 1, section: 'Preparación A', machine: 'PSJ-0A', type: 'HB', yarnTitle: '2/40', samples: ['22,45'], projections: { average: null } },
  ]

  it('updates only the selected sample cell without deriving server projections', () => {
    expect(updateSampleRecord(records, 'first', 2, '22,58')).toEqual([{
      ...records[0],
      samples: ['22,45', '', '22,58'],
    }])
  })
})
