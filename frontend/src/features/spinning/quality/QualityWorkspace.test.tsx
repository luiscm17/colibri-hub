import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { SpinningGateway } from '../integration/contracts'
import { unavailableSpinningGateway } from '../integration/unavailableGateway'
import { SpinningRoutePage } from '../routes'

Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })
Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', { writable: true, value: () => {} })

afterEach(cleanup)

describe('QualityWorkspace', () => {
  it('renders only server-authorized profile fields and preserves capture drafts', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" gateway={profileGateway} /></MantineProvider>)

    await selectQualityContext()
    const profile = await screen.findByRole('combobox', { name: 'Perfil de calidad' })
    const capture = await screen.findByLabelText('Captura de calidad')
    expect((profile as HTMLInputElement).value).toBe('Observación visual')
    const observation = within(capture).getByRole('textbox', { name: 'Observación visual' }) as HTMLInputElement
    fireEvent.change(observation, { target: { value: 'Hilo uniforme' } })

    expect(observation.value).toBe('Hilo uniforme')
    expect(screen.queryByText(/fórmula/i)).toBeNull()
    expect(screen.queryByText(/resultado/i)).toBeTruthy()
  })

  it('keeps the unavailable state available when the unavailable gateway is injected', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" gateway={unavailableSpinningGateway} /></MantineProvider>)

    expect(await screen.findByText(/no hay perfiles, campos de captura ni resultados disponibles/i)).toBeTruthy()
    expect((screen.getByRole('combobox', { name: 'Perfil de calidad' }) as HTMLInputElement).disabled).toBe(true)
    expect(screen.queryByLabelText('Captura de calidad')).toBeNull()
  })

  it('renders the authorized Sample profile grid through the default development gateway', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" /></MantineProvider>)

    await selectQualityContext()
    const profile = await screen.findByRole('combobox', { name: 'Perfil de calidad' })
    const grid = await screen.findByLabelText('Planilla de muestra de calidad')
    expect((profile as HTMLInputElement).value).toBe('Muestra autorizada')
    expect(grid.getAttribute('aria-rowcount')).toBe('13')
    expect(within(grid).getAllByRole('row').slice(1, 4).map(row => row.textContent)).toEqual([
      expect.stringContaining('Título'),
      expect.stringContaining('Resistencia'),
      expect.stringContaining('Elongación'),
    ])
  })

  it('renders configured sample measurements in server order with readonly results and tolerance status', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" gateway={sampleGateway} /></MantineProvider>)

    await selectQualityContext()
    const profile = await screen.findByRole('combobox', { name: 'Perfil de calidad' })
    const grid = await screen.findByLabelText('Planilla de muestra de calidad')
    expect((profile as HTMLInputElement).value).toBe('Muestra de hilado')
    expect(grid.getAttribute('aria-rowcount')).toBe('11')
    expect(grid.getAttribute('aria-colcount')).toBe('5')
    expect(within(grid).getAllByRole('row').slice(1).map(row => row.textContent)).toEqual([
      expect.stringContaining('Título'),
      expect.stringContaining('Resistencia'),
      expect.stringContaining('Elongación'),
      expect.stringContaining('Vellosidad'),
    ])
    expect(within(grid).getByText('Ne')).toBeTruthy()
  })

  it('shows capture context before profiles, filters authorized profiles, and only shows permitted profile fields', async () => {
    render(<MantineProvider><SpinningRoutePage workspace="quality" gateway={contextGateway} /></MantineProvider>)

    expect(await screen.findByLabelText('Contexto de captura de calidad')).toBeTruthy()
    expect((screen.getByRole('combobox', { name: 'Perfil de calidad' }) as HTMLInputElement).disabled).toBe(true)
    await selectQualityContext()

    expect((await screen.findByRole('combobox', { name: 'Perfil de calidad' }) as HTMLInputElement).value).toBe('Perfil de continuas')
    expect(screen.getByRole('combobox', { name: 'Máquina' })).toBeTruthy()
    expect(screen.queryByRole('combobox', { name: 'Título de hilo' })).toBeNull()

    await selectOption('Sección', 'Madejeras')
    expect((await screen.findByRole('combobox', { name: 'Perfil de calidad' }) as HTMLInputElement).value).toBe('Perfil de madejeras')
    expect(screen.queryByRole('combobox', { name: 'Máquina' })).toBeNull()
    expect(screen.getByRole('combobox', { name: 'Título de hilo' })).toBeTruthy()
  })
})

async function selectQualityContext() {
  await selectOption('Sección', 'Continuas')
  fireEvent.change(screen.getByLabelText('Fecha operativa'), { target: { value: '2026-09-01' } })
  await selectOption('Turno', 'Turno A')
  await selectOption('Inspector', 'Inspector 1')
}

async function selectOption(label: string, option: string) {
  fireEvent.click(await screen.findByRole('combobox', { name: label }))
  fireEvent.click(screen.getAllByRole('option', { name: option, hidden: true }).at(-1)!)
}

const profileGateway: SpinningGateway = {
  getIntegrationState: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getSectionContext: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProductionDischargeCatalog: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getProgressContinuity: async () => ({ status: 'unavailable', message: 'Not used.', retryable: false }),
  getQualityCaptureCatalog: async () => qualityCatalog,
  getQualityProfiles: async () => ({ status: 'populated', data: [{ id: 'observation', label: 'Observación visual', method: 'observation', captureContext: hiddenProfileContext, captureFields: [{ id: 'appearance', label: 'Observación visual', required: true }] }] }),
}

const sampleGateway: SpinningGateway = {
  ...profileGateway,
  getQualityProfiles: async () => ({ status: 'populated', data: [{
    id: 'sample', label: 'Muestra de hilado', method: 'sample', captureContext: hiddenProfileContext, measurements: [
      { id: 'count', label: 'Título', unit: 'Ne', required: true, validation: 'decimal', serverResult: '20,1', toleranceStatus: 'within-tolerance' },
      { id: 'strength', label: 'Resistencia', unit: 'cN/tex', required: true, validation: 'decimal', serverResult: '—', toleranceStatus: 'out-of-tolerance' },
      { id: 'elongation', label: 'Elongación', unit: '%', required: false, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
      { id: 'hairiness', label: 'Vellosidad', unit: 'H', required: true, validation: 'decimal', serverResult: '4,2', toleranceStatus: 'within-tolerance' },
      { id: 'evenness', label: 'Regularidad', unit: 'CV%', required: true, validation: 'decimal', serverResult: '11,3', toleranceStatus: 'within-tolerance' },
      { id: 'mass', label: 'Masa', unit: 'g', required: true, validation: 'decimal', serverResult: '1,4', toleranceStatus: 'within-tolerance' },
      { id: 'twist', label: 'Torsión', unit: 'vueltas/m', required: true, validation: 'integer', serverResult: '840', toleranceStatus: 'within-tolerance' },
      { id: 'shrinkage', label: 'Contracción', unit: '%', required: false, validation: 'decimal', serverResult: null, toleranceStatus: 'pending' },
      { id: 'color', label: 'Color', unit: 'grado', required: true, validation: 'text', serverResult: 'A', toleranceStatus: 'unavailable' },
      { id: 'humidity', label: 'Humedad', unit: '%', required: true, validation: 'decimal', serverResult: '7,4', toleranceStatus: 'out-of-tolerance' },
    ],
  }] }),
}

const qualityCatalog = { status: 'populated' as const, data: {
  sections: [{ id: 'ring-spinning', label: 'Continuas' }, { id: 'skeining', label: 'Madejeras' }],
  shifts: [{ id: 'A', label: 'Turno A' }],
  inspectors: [{ id: 'inspector-1', label: 'Inspector 1' }],
  machines: [{ id: 'machine-1', label: 'Máquina 1' }],
  yarnCounts: [{ id: '30-1', label: '30/1' }],
} }

const hiddenProfileContext = { machine: 'hidden' as const, applicableMachineIds: [], yarnCount: 'hidden' as const, applicableYarnCountIds: [] }

const contextGateway: SpinningGateway = {
  ...profileGateway,
  getQualityProfiles: async context => ({ status: 'populated', data: context.sectionId === 'ring-spinning'
    ? [{ id: 'ring', label: 'Perfil de continuas', method: 'observation', captureContext: { machine: 'required', applicableMachineIds: ['machine-1'], yarnCount: 'hidden', applicableYarnCountIds: [] }, captureFields: [] }]
    : [{ id: 'skeining', label: 'Perfil de madejeras', method: 'observation', captureContext: { machine: 'hidden', applicableMachineIds: [], yarnCount: 'optional', applicableYarnCountIds: ['30-1'] }, captureFields: [] }] }),
}
