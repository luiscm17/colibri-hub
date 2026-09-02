import { describe, expect, it } from 'vitest'
import { productionDischargeColumns } from './productionDischargeColumns'

describe('Preparation production grid', () => {
  it('renders the Finisor workbook schema without a yarn title or browser-calculated net weight', () => {
    const columns = productionDischargeColumns('preparation')

    expect(columns.map(column => column.name)).toEqual([
      'No', 'Máquina', 'Tipo', 'Peso Bruto', 'Núm. Mechas', 'Peso Cañete [kg]', 'Peso Tacho [kg]', 'Peso Neto [kg]', 'Observaciones',
    ])
    expect(columns.find(column => column.key === 'netWeightKg')?.editable).toBeUndefined()
    expect(columns.find(column => column.key === 'defaultPackageTareWeightKg')?.editable).toBeUndefined()
    expect(columns.find(column => column.key === 'defaultCartWeightKg')?.editable).toBeUndefined()
  })
})
