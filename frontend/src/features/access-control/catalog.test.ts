import { describe, expect, it } from 'vitest'
import { ACCESS_CATALOG, CORRECTION_REQUIREMENTS, requirementForPath } from './catalog'

describe('Access catalog', () => {
  it('declares independent exact requirements for every protected business capability', () => {
    expect(ACCESS_CATALOG['/warehouse/bales']).toEqual({ action: 'read', scope: 'warehouse.raw_materials' })
    expect(ACCESS_CATALOG['/warehouse/bales/delivery']).toEqual({ action: 'write', scope: 'warehouse.raw_materials' })
    expect(ACCESS_CATALOG['/spinning/ring-spinning']).toEqual({ action: 'read', scope: 'yarn_spinning.section.ring_spinning' })
    expect(ACCESS_CATALOG['/spinning/quality']).toEqual({ anyOf: [{ action: 'read', scope: 'yarn_spinning.process_quality' }, { action: 'write', scope: 'yarn_spinning.process_quality' }] })
    expect(ACCESS_CATALOG['/lots/queue']).toEqual({ action: 'read', scope: 'lot_processing' })
    expect(ACCESS_CATALOG['/lots/inventory']).toEqual({ anyOf: [{ action: 'read', scope: 'lot_processing.stage.inventory' }, { action: 'write', scope: 'lot_processing.stage.inventory' }] })
    expect(ACCESS_CATALOG['/spinning/consolidated']).toEqual({ action: 'read', scope: 'transversal.consolidated_dashboard' })
  })

  it('keeps ordinary and exceptional correction actions distinct', () => {
    expect(CORRECTION_REQUIREMENTS.edit).not.toEqual(CORRECTION_REQUIREMENTS.editOutsideWindow)
  })

  it('keeps the warehouse operation requirements exact', () => {
    expect(ACCESS_CATALOG['/warehouse/bales/reception']).toEqual({ action: 'write', scope: 'warehouse.raw_materials' })
    expect(ACCESS_CATALOG['/warehouse/bales/stock']).toEqual({ action: 'read', scope: 'warehouse.raw_materials' })
  })

  it('does not derive requirements from paths, filters, shifts, or action labels', () => {
    expect(requirementForPath('/spinning/ring-spinning?shift=night')).toEqual({ action: 'read', scope: 'yarn_spinning.section.ring_spinning' })
    expect(requirementForPath('/spinning/ring-spinning/edit')).toBeNull()
    expect(requirementForPath('/unknown')).toBeNull()
  })
})
