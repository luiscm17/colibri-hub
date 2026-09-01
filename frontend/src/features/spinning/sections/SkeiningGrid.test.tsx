import { MantineProvider } from '@mantine/core'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { SpinningRoutePage } from '../routes'
import type { SpinningGateway } from '../integration/contracts'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })

afterEach(cleanup)

describe('SkeiningGrid', () => {
  it('renders independent catalog-backed Skeining production without Progress or Lot Processing', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="skeining" gateway={catalogGateway} /></MantineProvider>)

    expect(await screen.findByLabelText('Skeining production grid')).toBeTruthy()
    expect(screen.getByRole('grid').getAttribute('aria-colcount')).toBe('7')
    expect(screen.getByRole('status').textContent).toContain('únicamente cuando el servidor confirme')
    expect(screen.queryByLabelText('Progress summary grid')).toBeNull()
    expect(screen.queryByText(/Procesamiento de lotes/i)).toBeNull()
  })
})

const catalogGateway: SpinningGateway = {
  getIntegrationState: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getSectionContext: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getProgressContinuity: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getQualityCaptureCatalog: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getQualityProfiles: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getProductionDischargeCatalog: async () => ({
    status: 'populated',
    data: {
      machines: [{ id: 'madejera-01', label: 'Madejera 01' }],
      applicableMachineIds: ['madejera-01'],
      rovingTitleApplicableMachineIds: [],
      yarnCounts: [{ id: '20/2', label: '20/2' }],
    },
  }),
}
