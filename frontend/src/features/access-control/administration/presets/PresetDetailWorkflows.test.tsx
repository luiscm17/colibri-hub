import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PresetDetailWorkflows } from './PresetDetailWorkflows'

const fetchMock = vi.fn((...args: unknown[]) => { void args; return Promise.resolve({ items: [], total: 0 }) })
vi.mock('@/api/httpClient', () => ({ httpJson: (...args: unknown[]) => fetchMock(...args) }))
Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) })
Object.defineProperty(window, 'ResizeObserver', { writable: true, value: class { observe() {} unobserve() {} disconnect() {} } })

afterEach(cleanup)

describe('PresetDetailWorkflows', () => {
  it('reports the OR of preset and copy draft dirtiness', async () => {
    const onDirtyChange = vi.fn()
    render(<MantineProvider><PresetDetailWorkflows preset={{ presetId: 'preset-1', presetCode: 'operator', presetName: 'Operator', description: null, isActive: true, version: 1, permissions: [] }} onDirtyChange={onDirtyChange} /></MantineProvider>)
    const name = await screen.findByLabelText('Preset name')
    fireEvent.change(screen.getByLabelText('Role code'), { target: { value: 'changed-copy' } })
    fireEvent.change(name, { target: { value: 'Changed preset' } })
    fireEvent.change(name, { target: { value: 'Operator' } })
    await waitFor(() => expect(onDirtyChange).toHaveBeenLastCalledWith(true))
  })
})
