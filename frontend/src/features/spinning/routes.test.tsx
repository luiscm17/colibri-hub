import { MantineProvider } from '@mantine/core'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { SpinningGateway } from './integration/contracts'
import { SectionWorkspace } from './sections/SectionWorkspace'
import { SpinningRoutePage } from './routes'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })

afterEach(cleanup)

describe('SpinningRoutePage', () => {
  it('identifies the selected Yarn Spinning workspace and its unavailable integration', () => {
    render(<MantineProvider><SpinningRoutePage workspace="skeining" /></MantineProvider>)

    expect(screen.getByRole('heading', { name: 'Skeining' })).toBeTruthy()
    expect(screen.getByRole('status').textContent).toContain('integration is unavailable')
    expect(screen.queryByText('Lot Processing')).toBeNull()
    expect(screen.queryByText(/confirmed|calculated/i)).toBeNull()
  })

  it('uses catalog applicability for Preparation machine and yarn-count selections', async () => {
    render(<MantineProvider><SectionWorkspace workspace="preparation" gateway={catalogGateway} /></MantineProvider>)

    const selections = await screen.findByLabelText('Available reference selections')
    expect(selections.textContent).toContain('FIN-01')
    expect(selections.textContent).not.toContain('PSJ-01')
    expect(selections.textContent).toContain('30/1')
    expect(screen.getByLabelText('Production Discharge grid')).toBeTruthy()
    expect(screen.queryByText('Applicable Progress')).toBeNull()
  })

  it('keeps catalog-dependent selections unavailable when production reference data is unavailable', async () => {
    render(<MantineProvider><SectionWorkspace workspace="preparation" /></MantineProvider>)

    expect(await screen.findByText('Machine and yarn-count selections are unavailable until reference data is available.')).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Add discharge' }) as HTMLButtonElement).disabled).toBe(true)
  })
})

const catalogGateway: SpinningGateway = {
  getIntegrationState: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getSectionContext: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getProgressContinuity: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getProductionDischargeCatalog: async () => ({
    status: 'populated',
    data: {
      machines: [{ id: 'FIN-01', label: 'FIN-01' }, { id: 'PSJ-01', label: 'PSJ-01' }],
      applicableMachineIds: ['FIN-01'],
      yarnCounts: [{ id: '30/1', label: '30/1' }],
    },
  }),
}
