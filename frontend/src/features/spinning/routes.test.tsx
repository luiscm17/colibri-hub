import { MantineProvider } from '@mantine/core'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { SpinningGateway } from './integration/contracts'
import { SectionWorkspace } from './sections/SectionWorkspace'
import { hasRovingTitleInput, rovingTitleMachineIds } from './sections/configuration'
import { SpinningRoutePage } from './routes'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })

afterEach(cleanup)

describe('SpinningRoutePage', () => {
  it('identifies the selected Skeining workspace without Progress or Lot Processing', () => {
    render(<MantineProvider><SpinningRoutePage workspace="skeining" /></MantineProvider>)

    expect(screen.getByRole('heading', { name: 'Madejeras' })).toBeTruthy()
    expect(screen.getByLabelText('Skeining production grid')).toBeTruthy()
    expect(screen.queryByText('Procesamiento de lotes')).toBeNull()
    expect(screen.queryByLabelText('Progress summary grid')).toBeNull()
  })

  it('uses catalog-backed identities and shows Progress for Preparation', async () => {
    render(<MantineProvider><SectionWorkspace workspace="preparation" gateway={catalogGateway} /></MantineProvider>)

    const selections = await screen.findByLabelText('Available reference selections')
    expect(selections.textContent).toContain('FIN-01')
    expect(selections.textContent).not.toContain('PSJ-01')
    expect(selections.textContent).toContain('30/1')
    expect(screen.getByLabelText('Production Discharge grid')).toBeTruthy()
    expect(rovingTitleMachineIds(catalogGatewayData)).toEqual(['FIN-01'])
    expect(hasRovingTitleInput(catalogGatewayData)).toBe(true)
    expect(screen.getByLabelText('Progress summary grid')).toBeTruthy()
  })

  it.each(['ringSpinning', 'bobbinWinding', 'twisting'] as const)('does not authorize the roving title input for %s when its catalog does not authorize it', async (workspace) => {
    render(<MantineProvider><SectionWorkspace workspace={workspace} gateway={catalogGatewayWithoutRovingTitle} /></MantineProvider>)

    expect(await screen.findByLabelText('Production Discharge grid')).toBeTruthy()
    expect(rovingTitleMachineIds(catalogGatewayWithoutRovingTitleData)).toEqual([])
    expect(hasRovingTitleInput(catalogGatewayWithoutRovingTitleData)).toBe(false)
  })

  it('renders the operational supervisor capture context and operational shift values', async () => {
    render(<MantineProvider><SectionWorkspace workspace="preparation" gateway={catalogGateway} /></MantineProvider>)

    expect((screen.getByLabelText('Contexto de captura') as HTMLSelectElement).value).toBe('operational-supervisor')
    expect((screen.getByLabelText('Contexto de captura') as HTMLSelectElement).disabled).toBe(true)
    expect(screen.getByText(/se aplicará a los registros cuando el servicio autorice/i)).toBeTruthy()
    expect([...((screen.getByLabelText('Turno') as HTMLSelectElement).options)].map(option => option.value)).toEqual(['', 'A', 'B', 'C'])
    expect(await screen.findByLabelText('Production Discharge grid')).toBeTruthy()
  })

  it('keeps catalog-dependent selections unavailable when production reference data is unavailable', async () => {
    render(<MantineProvider><SectionWorkspace workspace="preparation" /></MantineProvider>)

    expect(await screen.findByText('Las selecciones de máquina y título de hilo no están disponibles hasta que los datos de referencia estén disponibles.')).toBeTruthy()
    expect((screen.getByRole('button', { name: 'Agregar descarga' }) as HTMLButtonElement).disabled).toBe(true)
  })
})

const catalogGateway: SpinningGateway = {
  getIntegrationState: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getSectionContext: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getProgressContinuity: async () => ({ status: 'unavailable', message: 'Not used by this grid.', retryable: false }),
  getProductionDischargeCatalog: async () => ({
    status: 'populated',
    data: {
      ...catalogGatewayData,
    },
  }),
}

const catalogGatewayData = {
  machines: [{ id: 'FIN-01', label: 'FIN-01' }, { id: 'PSJ-01', label: 'PSJ-01' }],
  applicableMachineIds: ['FIN-01'],
  rovingTitleApplicableMachineIds: ['FIN-01'],
  yarnCounts: [{ id: '30/1', label: '30/1' }],
} as const

const catalogGatewayWithoutRovingTitle: SpinningGateway = {
  ...catalogGateway,
  getProductionDischargeCatalog: async () => ({
    status: 'populated',
    data: catalogGatewayWithoutRovingTitleData,
  }),
}

const catalogGatewayWithoutRovingTitleData = {
  machines: [{ id: 'machine-01', label: 'Máquina 01' }],
  applicableMachineIds: ['machine-01'],
  rovingTitleApplicableMachineIds: [],
  yarnCounts: [{ id: '30/1', label: '30/1' }],
} as const
