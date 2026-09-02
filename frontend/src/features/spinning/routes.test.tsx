import { MantineProvider } from '@mantine/core'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { SpinningGateway } from './integration/contracts'
import { unavailableSpinningGateway } from './integration/unavailableGateway'
import { SectionWorkspace } from './sections/SectionWorkspace'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })
afterEach(cleanup)

describe('SectionWorkspace', () => {
  it('renders fixed gateway roster rows and the required header', async () => {
    render(<MantineProvider><SectionWorkspace workspace="ringSpinning" gateway={catalogGateway} /></MantineProvider>)

    expect(await screen.findByLabelText('Production roster grid')).toBeTruthy()
    expect(screen.getByLabelText('Progress roster grid')).toBeTruthy()
    expect(screen.getByLabelText('Turno')).toBeTruthy()
    expect(screen.getByLabelText('Supervisor')).toBeTruthy()
    expect(screen.getByLabelText('Fecha')).toBeTruthy()
    expect(screen.getByLabelText('Encargado')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /agregar/i })).toBeNull()
  })

  it('renders the Madejeras production schema without Progress', async () => {
    render(<MantineProvider><SectionWorkspace workspace="skeining" gateway={catalogGateway} /></MantineProvider>)

    expect(await screen.findByLabelText('Production roster grid')).toBeTruthy()
    expect(screen.getByText('Las filas del roster y las proyecciones son suministradas por el servicio.')).toBeTruthy()
    expect(screen.queryByLabelText('Progress roster grid')).toBeNull()
  })

  it('renders only the Finisor production table for Preparation', async () => {
    render(<MantineProvider><SectionWorkspace workspace="preparation" gateway={catalogGateway} /></MantineProvider>)

    expect(await screen.findByLabelText('Production roster grid')).toBeTruthy()
    expect(screen.queryByLabelText('Progress roster grid')).toBeNull()
  })

  it('keeps roster injection unavailable when the unavailable gateway is supplied', async () => {
    render(<MantineProvider><SectionWorkspace workspace="preparation" gateway={unavailableSpinningGateway} /></MantineProvider>)

    expect(await screen.findByText('El roster de producción no está disponible hasta que el servicio esté disponible.')).toBeTruthy()
  })
})

const catalogGateway: SpinningGateway = {
  getIntegrationState: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getSectionContext: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProgressContinuity: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualityCaptureCatalog: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualityProfiles: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualitySampleRecords: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProductionDischargeCatalog: async () => ({ status: 'populated', data: {
    productionRoster: [{ id: 'production-1', number: 1, machine: 'Continua 01', yarnTitle: '30/1', type: 'Algodón', defaultPackageTareWeightKg: '0.20', defaultCartWeightKg: '1.50', projections: { netWeightKg: '12.5' } }],
    progressRoster: [{ id: 'progress-1', number: 1, machine: 'Continua 01', yarnTitle: '30/1', type: 'Algodón', projections: {} }],
  } }),
}
