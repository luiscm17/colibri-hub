import { MantineProvider } from '@mantine/core'
import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { SpinningGateway } from '../integration/contracts'
import { unavailableSpinningGateway } from '../integration/unavailableGateway'
import { SpinningRoutePage } from '../routes'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })
Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', { writable: true, value: () => {} })

afterEach(cleanup)

describe('QualityWorkspace', () => {
  it('renders the worksheet operational header and transversal sample grid from the development gateway', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" /></MantineProvider>)

    const grid = await screen.findByLabelText('Planilla de muestra de calidad')
    const header = screen.getByLabelText('Contexto de captura de calidad')
    expect(within(header).getByText('Turno')).toBeTruthy()
    expect(within(header).getByText('Supervisor')).toBeTruthy()
    expect(within(header).getByText('Fecha')).toBeTruthy()
    expect(within(header).getByText('Analista')).toBeTruthy()
    expect(screen.queryByLabelText('Sección')).toBeNull()
    expect(grid.getAttribute('aria-rowcount')).toBe('3')
    expect(grid.getAttribute('aria-colcount')).toBe('26')
    expect(within(grid).getAllByRole('row')[1].textContent).toContain('Preparación A')
    expect(within(grid).getAllByRole('row')[1].textContent).toContain('PSJ-0A')
  })

  it('uses profile-defined sample and result columns and omits unsupported observations', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" gateway={sampleGateway} /></MantineProvider>)

    const grid = await screen.findByLabelText('Planilla de muestra de calidad')
    expect(grid.getAttribute('aria-colcount')).toBe('17')
    expect(screen.queryByText(/=AVERAGE|#VALUE!/i)).toBeNull()
  })

  it('keeps the unavailable state injectable', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" gateway={unavailableSpinningGateway} /></MantineProvider>)

    expect(await screen.findByText(/no hay perfiles, campos de captura ni resultados disponibles/i)).toBeTruthy()
    expect(screen.queryByLabelText('Planilla de muestra de calidad')).toBeNull()
  })
})

const sampleGateway: SpinningGateway = {
  defaultQualityCaptureContext: { businessDate: '2026-09-01', shiftId: 'A', supervisorId: 'supervisor', analystId: 'analyst' },
  getIntegrationState: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getSectionContext: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProductionDischargeCatalog: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProgressContinuity: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualityCaptureCatalog: async () => ({ status: 'populated', data: { shifts: [{ id: 'A', label: 'Turno A' }], supervisors: [{ id: 'supervisor', label: 'Supervisor' }], analysts: [{ id: 'analyst', label: 'Analista' }] } }),
  getQualityProfiles: async () => ({ status: 'populated', data: [{ id: 'sample', label: 'Muestra de hilado', method: 'sample', sampleCount: 10, resultColumns: [{ id: 'average', label: 'Promedio' }, { id: 'std-error', label: 'Error STD' }], supportsObservations: false }] }),
  getQualitySampleRecords: async () => ({ status: 'populated', data: [{ id: 'record-1', number: 1, section: 'Preparación A', machine: 'PSJ-0A', type: 'HB', yarnTitle: '2/40', samples: [], projections: { average: null, 'std-error': null } }] }),
}
