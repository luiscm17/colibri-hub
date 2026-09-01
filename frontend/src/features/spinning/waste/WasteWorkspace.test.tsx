import { MantineProvider } from '@mantine/core'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { SpinningGateway } from '../integration/contracts'
import { unavailableSpinningGateway } from '../integration/unavailableGateway'
import { WasteWorkspace } from './WasteWorkspace'
import { createWasteDraft } from './wasteModel'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })

afterEach(cleanup)

describe('WasteWorkspace', () => {
  it('renders the worksheet-shaped waste grid with gateway-provided context and no calculated columns', async () => {
    renderWorkspace(catalogGateway)

    expect(await screen.findByLabelText('Waste capture grid')).toBeTruthy()
    expect(screen.getByRole('grid').getAttribute('aria-colcount')).toBe('5')
    expect(screen.getByLabelText('Contexto operativo de desperdicio').textContent).toContain('Turno: A')
    expect(screen.getByLabelText('Contexto operativo de desperdicio').textContent).toContain('Supervisor: JUNIOR')
    expect(screen.getByLabelText('Contexto operativo de desperdicio').textContent).toContain('Encargado: RICHARD')
    expect(screen.getByText('CONT-0A, CONT-0B, CONT-1A')).toBeTruthy()
    expect(screen.getAllByText('Pendiente de confirmación del servidor').length).toBeGreaterThan(0)
    expect(screen.queryByText(/teórico|acumulado/i)).toBeNull()
    expect(screen.getByText(/madejas fuera de especificación se reprocesan/i)).toBeTruthy()
  })

  it('keeps the waste grid unavailable when the unavailable gateway is injected', async () => {
    renderWorkspace(unavailableSpinningGateway)

    expect(await screen.findByText('Las referencias de desperdicio no están disponibles hasta que el servicio esté disponible.')).toBeTruthy()
    expect(screen.queryByLabelText('Contexto operativo de desperdicio')).toBeNull()
  })

  it('keeps only gateway-authorized machine-group rows in the local draft', () => {
    const draft = createWasteDraft([{ id: 'group-a', number: 1, section: 'Continuas', machine: 'CONT-0A, CONT-0B', weightKg: '' }])
    expect(draft.rows).toEqual([{ rowId: 'group-a', number: 1, section: 'Continuas', machine: 'CONT-0A, CONT-0B', weightKg: '' }])
  })
})

function renderWorkspace(gateway: SpinningGateway) {
  return render(<MantineProvider><WasteWorkspace gateway={gateway} /></MantineProvider>)
}

const catalogGateway: SpinningGateway = {
  getIntegrationState: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getSectionContext: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProductionDischargeCatalog: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProgressContinuity: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualityCaptureCatalog: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualityProfiles: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualitySampleRecords: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getWasteCaptureCatalog: async () => ({ status: 'populated', data: { context: { shift: 'A', supervisor: 'JUNIOR', businessDate: '2026-05-03', recorder: 'RICHARD' }, rows: [{ id: 'ring-group', number: 1, section: 'Continuas', machine: 'CONT-0A, CONT-0B, CONT-1A', weightKg: '' }], totalKg: null } }),
}
