import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MantineProvider } from '@mantine/core'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import type { DashboardFilters, DashboardProjection, SpinningGateway } from '../integration/contracts'
import { ReportingWorkspace } from './ReportingWorkspace'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })

const projection: DashboardProjection = { sections: [{ section: 'Preparación', metrics: [{ name: 'total_discharged_kg', value: '12.50', unit: 'kg', availability: 'available' }, { name: 'real_waste_kg', value: '0', unit: 'kg', availability: 'zero' }, { name: 'average_discharge_kg', value: null, unit: 'kg', availability: 'unavailable', reason: 'Pendiente del servidor' }] }] }
const gateway = (getDashboard: SpinningGateway['getDashboard']): SpinningGateway => ({ getIntegrationState: async () => ({ status: 'empty' }), getSectionContext: async () => ({ status: 'empty' }), getProductionDischargeCatalog: async () => ({ status: 'empty' }), getProgressContinuity: async () => ({ status: 'empty' }), getQualityCaptureCatalog: async () => ({ status: 'empty' }), getQualityProfiles: async () => ({ status: 'empty' }), getQualitySampleRecords: async () => ({ status: 'empty' }), getDashboard })
const renderWorkspace = (getDashboard: SpinningGateway['getDashboard']) => render(<MantineProvider><MemoryRouter initialEntries={['/?shift=A']}><ReportingWorkspace gateway={gateway(getDashboard)} section="Preparación" /></MemoryRouter></MantineProvider>)

describe('ReportingWorkspace', () => {
  it('retains URL filters and renders server-returned metrics without substituting unavailable values', async () => {
    const getDashboard = vi.fn(async (filters: DashboardFilters) => ({ status: 'populated' as const, data: projection, filters }))
    renderWorkspace(getDashboard)
    expect(await screen.findByText('12.50 kg')).toBeTruthy()
    expect(screen.getByText('Pendiente del servidor')).toBeTruthy()
    expect(screen.getByText('Disponibilidad: Cero confirmado')).toBeTruthy()
    await userEvent.clear(screen.getByLabelText('Turno'))
    await userEvent.type(screen.getByLabelText('Turno'), 'B')
    await waitFor(() => expect(getDashboard).toHaveBeenLastCalledWith(expect.objectContaining({ shift: 'B' }), 'Preparación', expect.any(AbortSignal)))
  })

  it('announces loading while the server projection is pending', async () => {
    renderWorkspace(() => new Promise(() => {}))
    expect(await screen.findByText('Cargando resultados del reporte…')).toBeTruthy()
  })

  it.each([
    [{ status: 'empty' }],
    [{ status: 'unavailable', message: 'Servicio no disponible', retryable: false }],
    [{ status: 'failure', message: 'Error recuperable' }],
    [{ status: 'stale', data: projection, message: 'Resultados anteriores' }],
  ] as const)('distinguishes reporting state %#', async (result) => {
    renderWorkspace(async () => result)
    if (result.status === 'empty') expect(await screen.findByText(/No hay datos de origen/)).toBeTruthy()
    if (result.status === 'unavailable') expect(await screen.findByText('Servicio no disponible')).toBeTruthy()
    if (result.status === 'failure') expect(await screen.findByRole('button', { name: 'Reintentar' })).toBeTruthy()
    if (result.status === 'stale') expect(await screen.findByText('Resultados anteriores')).toBeTruthy()
  })
})
