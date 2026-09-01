import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { SpinningGateway } from '../integration/contracts'
import { SpinningRoutePage } from '../routes'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })
Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', { writable: true, value: () => {} })

afterEach(cleanup)

describe('QualityWorkspace', () => {
  it('renders only server-authorized profile fields and preserves capture drafts across profile refreshes', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" gateway={profileGateway} /></MantineProvider>)

    const profile = await screen.findByRole('combobox', { name: 'Perfil de calidad' })
    fireEvent.click(profile)
    fireEvent.click(document.querySelector('[data-combobox-option]')!)
    const capture = await screen.findByLabelText('Captura de calidad')
    const observation = within(capture).getByRole('textbox', { name: 'Observación visual' }) as HTMLInputElement
    fireEvent.change(observation, { target: { value: 'Hilo uniforme' } })

    expect(observation.value).toBe('Hilo uniforme')
    expect(screen.queryByText(/fórmula/i)).toBeNull()
    expect(screen.queryByText(/resultado/i)).toBeTruthy()
  })

  it('does not invent quality fields or results while profiles are unavailable', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" /></MantineProvider>)

    expect(await screen.findByText(/no hay perfiles, campos de captura ni resultados disponibles/i)).toBeTruthy()
    expect((screen.getByRole('combobox', { name: 'Perfil de calidad' }) as HTMLInputElement).disabled).toBe(true)
    expect(screen.queryByLabelText('Captura de calidad')).toBeNull()
  })
})

const profileGateway: SpinningGateway = {
  getIntegrationState: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getSectionContext: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProductionDischargeCatalog: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProgressContinuity: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualityProfiles: async () => ({ status: 'populated', data: [{ id: 'observation', label: 'Observación visual', method: 'observation', captureFields: [{ id: 'appearance', label: 'Observación visual', required: true }] }] }),
}
